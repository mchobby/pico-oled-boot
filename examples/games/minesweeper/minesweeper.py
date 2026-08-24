# MineSweeper game for Pico-Oled_boot
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from micropython import const
from oledboot import *
from menuboot import MenuBoot
from fbutil import FBUtil
from fbtext import *
from font5x4 import Font5X4
import machine, random, time, framebuf, sys

random.seed( machine.ADC(machine.Pin(28)).read_u16() )


TILE_W = 8  # Size of a tile
TILE_H = 8
XTILES = 15 # Nbr of tile displayed on X axis 
YTILES = 7
XOFF   = 2 # Start AREA Display XOffset pixels in screen
YOFF   = 2

FLAGGED_STATE = 70 # =F (used in Cell.state)

DIR_CHECK = 100 # Special DIR value for button B
DIR_FLAG  = 101 # Special DIR value for button A

REPEAT_MS = 100 # Time to repeat an input
ANIM_MS   = 250 # Time between 2 animation steps

# minesweeper.pbm - 64 x 64 pixels
# Ressource for FBGFX fbutil.py : FBUtil.draw_bitmap() 
# Call fbutil_obj.draw_bitmap( x, y, LOGO, 64, 64, 1 )
LOGO = [ 0,0,0,3,192,0,0,0, 0,0,0,3,192,0,0,0, 0,0,0,12,240,0,0,0, 0,0,0,28,248,0,0,0,
	0,0,0,28,248,0,0,0,	0,0,0,28,248,0,0,0, 0,0,0,12,240,0,0,0, 0,0,1,255,255,128,0,0,
	0,0,1,255,255,128,0,0, 0,124,62,0,0,124,62,0, 0,124,62,0,8,124,62,0, 1,242,200,0,0,42,206,128,
	1,227,192,0,0,3,199,128, 1,227,192,0,32,19,199,128, 1,255,0,20,10,71,255,128, 1,255,2,8,2,3,255,128, 
	0,124,0,96,144,100,254,0, 0,124,0,36,2,32,254,0, 0,96,0,1,40,88,254,0, 0,96,0,144,2,76,254,0,
	0,96,2,36,144,114,254,0, 0,96,0,84,46,120,254,0, 0,96,34,40,146,116,254,0, 1,130,145,86,170,135,127,128,
	1,128,161,84,170,151,191,128, 1,128,10,31,234,170,127,128, 1,128,4,95,213,85,127,128, 27,128,70,100,252,171,191,216,
	63,144,73,96,58,171,127,252, 63,128,70,224,189,87,127,252, 193,130,41,96,126,245,255,215, 193,131,42,224,190,114,255,203,
	255,128,5,117,255,189,255,255, 255,128,34,244,255,158,255,255, 63,128,10,191,255,235,191,252, 63,129,66,159,255,151,127,252,
	61,192,21,127,255,235,255,244, 1,240,42,135,255,247,255,128, 1,229,42,183,255,247,255,128, 1,244,47,119,255,222,255,128,
	1,244,22,247,255,189,255,128, 0,127,213,221,127,127,254,0, 0,124,235,190,190,255,254,0, 0,127,127,247,191,255,254,0,
	0,127,190,119,79,159,254,0, 0,127,127,115,111,191,254,0, 0,31,251,255,255,255,248,0, 0,31,253,231,255,255,248,0,
	0,31,255,255,255,255,240,0, 0,31,255,255,255,255,248,0, 0,119,255,255,255,255,238,0, 0,119,255,255,255,255,238,0,
	0,123,255,255,255,255,246,0, 0,127,255,255,255,255,254,0, 0,127,255,255,255,255,254,0, 0,31,1,255,255,128,248,0,
	0,31,1,255,255,128,248,0, 0,0,0,31,120,0,0,0, 0,0,0,31,184,0,0,0, 0,0,0,31,184,0,0,0,
	0,0,0,31,112,0,0,0, 0,0,0,31,184,0,0,0, 0,0,0,3,192,0,0,0, 0,0,0,3,192,0,0,0]


class Coord:
	__slots__ = ('x','y')
	def __init__( self ):
		self.x=0
		self.y=0
	def __repr__( self ):
		return "<%s %i,%i>" % (self.__class__.__name__, self.x, self.y)

class Cell:
	__slots__ = ("state","bomb","x","y")
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.state = None # None=Not inspected, F=Flagged, 0=Inspected no bomb around, 1..8=# of bomb around
		self.mine  = False # A mine is present under the cell
	def __repr__(self):
		return "<%s %s,%s state=%r mine=%r>" % (self.__class__.__name__, self.x, self.y, self.state, self.mine)

class GameBoard( list ):
	def __init__( self, width, height ):
		super().__init__()
		self.width = width
		self.height = height
		self.mines = [] # Qwick reference to the mines
		self.clear()

	def init( self, mines ):
		# mines; nbr of mines to seed 

		# Initialize a new GameBoard
		super().clear()
		for i in range( self.width*self.height ):
			self.append( Cell( x=(i%self.width), y=(i//self.width) ))
		# Let's seed the mines
		self.mines.clear()
		while mines>0:
			x = random.randint(0,self.width-1)
			y = random.randint(0,self.height-1)
			c = self.cells(x,y)
			if c.mine==True:
				continue
			c.mine = True
			self.mines.append( c )
			mines -= 1

	def cells( self, x, y ):
		return self[y*self.width+x]


class Gameset:
	""" Defining the characteristic of a game """
	__slots__ = ('name','width','height','mines')
	def __init__( self, name, width, height, mines ):
		self.name=name
		self.width=width
		self.height=height
		self.mines=mines


# List of various games configuration
# Newbies filled at 4% of mines,  Beginner at 7.5%, Skilled at 10%, Average at 15%, Expert at 20%
GAMESETS = [ Gameset('Newbie 15x15',15,15,13), Gameset('Beginner 20x20',20,20,30), Gameset('Skilled 20x20',30,20,40), Gameset('Skilled 30x20',30,20,60), \
			 Gameset('Average 20x20',20,20,60), Gameset('Average 30x30',30,20,135), Gameset('Expert 20x20',30,20,80), Gameset('Expert 30x30',30,30,180)  ]

class Game(OledBoot):
	def __init__( self ):
		super().__init__() # Add rotate as needed
		self.fbtls   = FBUtil( self )
		self.text_drawer = FBText( self, self.width, self.height, Font5X4() )
		
		# Selected Game configuration
		self.gameset = GAMESETS[0]

		self.board = None # Gameboard
		self.p = Coord() # Player Coordinate
		self.prel= Coord() # Relative coordinate of Player on thje screen
		self.tlc = Coord() # Coordinate of Top-Left Cell appearing on the screen
		self.init_game() # Initialize the variable?

	def show_intro(self):
		self.fill(0)
		self.fbtls.draw_bitmap( 64, 0, LOGO, 64, 64, 1 )
		self.text( "MineSweeper", 0, 0 ) #(self.width-11*8)//2, self.height//4 )
		#self.text( "Invaders", (self.width-9*8)//2, self.height//4+10 )		
		self.text_drawer.text("A  to flag", 8, 64-30-10, 1)
		self.text_drawer.text("B  to inspect", 8, 64-20-10, 1)
		self.text_drawer.text("Keep safe !", 8, 64-8-10, 1)
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)

	def select_level( self ):
		time.sleep_ms( 500 ) # Avoids accidental selection
		menu = MenuBoot( self )
		for idx, gameset in enumerate(GAMESETS):
			menu.add_label( idx, gameset.name )

		menu.start()
		while True:
			menu.update()
			entry=menu.selected
			if entry:
				# entry.code = index in GAMESET
				print( '%s selected' % entry )
				self.gameset = GAMESETS[ entry.code ]
				break

	def show_winner( self ):
		self.fill_rect( 25, 16, 78, 36, 0 )	
		self.rect( 26, 17, 76, 34, 1 )	
		self.text( "You  Win!", 28, 21)
		self.text_drawer.text( "Score: %i" % len(self.board.mines), 40, 29, 1 )
		self.text_drawer.text( "Press key", 45, 39, 1 )
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)		

	def show_gameover( self ):
		self.fill_rect( 25, 16, 78, 36+7, 0 )	
		self.rect( 26, 17, 76, 34+7, 1 )	
		self.text( "GAME OVER", 28, 21)
		self.text_drawer.text( "score: %i / %i" % ( len( list([mine for mine in self.board.mines if mine.state==FLAGGED_STATE]) ), len(self.board.mines) ), 40, 30, 1 ) 
		self.text_drawer.text( "Any key to explore", 28, 39, 1 )
		self.text_drawer.text( "start = new game", 28, 39+8, 1 )
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)		

	def init_game( self ):
		self.score = 0
		self.last_frame = time.ticks_ms()
		self.board = GameBoard( self.gameset.width, self.gameset.height )
		self.board.init( self.gameset.mines )
		self.p.x = self.board.width//2
		self.p.y = self.board.height//2
		self.last_dir = 0
		self.last_dir_time = time.ticks_ms()
		self.last_anim = time.ticks_ms() # Last time the anim step had been change
		self.anim_step  = 0 # from 0 to 7
		self.gameover = False

	def discover( self, cell ):	
		def check_around( cell ):
			""" Return the tuple (cnt,_l) : count of mine around + list of cells to check """
			cnt = 0
			_list  = []
			for xx in range(3):
				for yy in range(3):
					if (xx==1) and (yy==1):
						continue
					_x = cell.x-1+xx
					_y = cell.y-1+yy					
					if not( 0 <= _x < self.board.width ):
						continue
					if not( 0 <= _y < self.board.height ):
						continue
					c = self.board.cells( _x, _y )					
					if c.mine==True:
						cnt+=1
					if c.state==None:
						# if not( c in _list ):
						_list.append( c )
			return (cnt,_list)

		full_lst = [] # Other coorinate to check
		# Check all cells around the current one
		print( "Discover", cell )
		cnt, _l = check_around( cell )
		cell.state = cnt		
		if cnt==0:
			full_lst.extend(_l)
		while len(full_lst)>0:
			c = full_lst.pop()
			cnt, _l = check_around( c )
			c.state = cnt
			if cnt==0:
				full_lst.extend( _l )


  	def draw_frame( self ):
		now = time.ticks_ms()

		if time.ticks_diff( now, self.last_anim )>ANIM_MS:
			self.anim_step += 1
			if self.anim_step>7:
				self.anim_step=0
			self.last_anim=now

		# === User Input ===
		dir = self.dir # Only one request
		if self.button_b.pressed: # is signaled only once			
			dir = DIR_CHECK # open the cell
		elif self.button_a.pressed:
			dir = DIR_FLAG  # Place a flag on the cell
		self.last_frame = now

		# === Actions ===
		if (dir!=self.last_dir) or (time.ticks_diff(now,self.last_dir_time)>REPEAT_MS):
			if (dir==START) and self.gameover:
				return False
			if dir==RIGHT:
				self.p.x+=1
				if self.p.x>(self.board.width-1):
					self.p.x = (self.board.width-1)
			elif dir==LEFT:
				self.p.x-=1
				if self.p.x<0:
					self.p.x=0
			elif dir==UP:
				self.p.y-=1
				if self.p.y<0:
					self.p.y=0
			elif dir==DOWN:
				self.p.y+=1
				if self.p.y>(self.board.height-1):
					self.p.y = (self.board.height-1 )
			elif (dir==DIR_FLAG) and not(self.gameover):
				c = self.board.cells(self.p.x, self.p.y)
				if (c.state==None) or (c.state==FLAGGED_STATE):
					c.state = FLAGGED_STATE if c.state==None else None
				print( "flagged", c, "@", self.p )
			elif (dir==DIR_CHECK) and not(self.gameover):
				c = self.board.cells(self.p.x, self.p.y)			
				print( "check", c, "@", self.p )
				if c.mine:
					self.show_gameover() 
					# Set the game at GameOver,
					# Show Score and remaining Mines
					self.gameover = True										
				else:
					self.discover( c )

			self.last_dir = dir
			self.last_dir_time = now

		
		# === User Coordinate ===
		self.tlc.x = self.p.x-(XTILES//2) # top-left cell (of screen)
		self.tlc.y = self.p.y-(YTILES//2)
		self.prel.x = XTILES//2
		self.prel.y = YTILES//2
		# Reajust position when tlc is negative
		if self.tlc.x<0:
			self.prel.x -= abs(self.tlc.x)
			self.tlc.x = 0
		if self.tlc.y<0:
			self.prel.y -= abs(self.tlc.y)
			self.tlc.y=0
		# Reajust position when tlc+XY_tiles > board.width_height
		if (self.tlc.x+XTILES) > (self.board.width):
			delta = self.tlc.x+XTILES-self.board.width
			self.prel.x += delta
			self.tlc.x = self.board.width-XTILES
		if (self.tlc.y+YTILES) > (self.board.height):
			delta = self.tlc.y+YTILES-self.board.height
			self.prel.y += delta
			self.tlc.y = self.board.height-YTILES
		# print( "TLC", self.tlc, "p", self.p, "prel", self.prel )

		# === Draw Screen ===
		self.fill(0)
		
		for y in range( YTILES ):			
			for x in range( XTILES ):
				c = self.board.cells((self.tlc.x+x),(self.tlc.y+y))
				x_pixel = XOFF+1+x*TILE_W
				y_pixel = YOFF+1+y*TILE_H				
				if (c.state==None) and not self.gameover: # Not inspected
					if self.anim_step == 0:
						self.pixel(x_pixel  , y_pixel+2, 1)
						self.hline(x_pixel+1, y_pixel+1, 2, 1)
						self.pixel(x_pixel+3, y_pixel+2, 1 )
						self.hline(x_pixel+4, y_pixel+3, 3, 1)
						self.pixel(x_pixel+7, y_pixel+3, 1)				
					elif self.anim_step==1:
						self.hline(x_pixel+0, y_pixel+2, 2, 1)
						self.pixel(x_pixel+3, y_pixel+3, 1)
						self.pixel(x_pixel+4, y_pixel+2, 1)
						self.hline(x_pixel+6, y_pixel+3, 2, 1)
					elif self.anim_step==2:
						self.pixel(x_pixel+1, y_pixel+2, 1)
						self.pixel(x_pixel+3, y_pixel+3, 1)
						#self.pixel(x_pixel+4, y_pixel+2, 1)
						self.pixel(x_pixel+6, y_pixel+3, 1)
						#self.pixel(x_pixel+7, y_pixel+3, 1)
					elif self.anim_step==3:
						self.hline(x_pixel+0, y_pixel+2, 2, 1)
						self.pixel(x_pixel+3, y_pixel+3, 1)
						self.pixel(x_pixel+4, y_pixel+2, 1)
						self.hline(x_pixel+6, y_pixel+3, 2, 1)
					elif self.anim_step==4:
						self.pixel(x_pixel  , y_pixel+1, 1)
						self.pixel(x_pixel+1, y_pixel+2, 1)
						self.hline(x_pixel+2, y_pixel+3, 3, 1 )
						self.hline(x_pixel+5, y_pixel+2, 2, 1 )
						self.pixel(x_pixel+7, y_pixel+1, 1)							
					elif self.anim_step==5:
						self.hline(x_pixel+0, y_pixel+3+3, 2, 1)
						self.pixel(x_pixel+3, y_pixel+2+2, 1)
						self.pixel(x_pixel+4, y_pixel+3+3, 1)
						self.hline(x_pixel+6, y_pixel+2+2, 2, 1)
					elif self.anim_step==6:
						self.pixel(x_pixel+1+2, y_pixel+2+1, 1)
						self.pixel(x_pixel+3+2, y_pixel+3+1, 1)
						#self.pixel(x_pixel+4, y_pixel+2, 1)
						self.pixel(x_pixel+6+1, y_pixel+3+1, 1)
						#self.pixel(x_pixel+7, y_pixel+3, 1)
					elif self.anim_step==7:
						self.hline(x_pixel+0, y_pixel+2, 2, 1)
						self.pixel(x_pixel+3, y_pixel+3, 1)
						self.pixel(x_pixel+4, y_pixel+2, 1)
						self.hline(x_pixel+6, y_pixel+3, 2, 1)
				elif c.state==FLAGGED_STATE: # User placed a Flag!					
					if self.anim_step in (0,5):
						self.rect(x_pixel,y_pixel,2,8,1)
						self.hline(x_pixel+2, y_pixel  ,3,1)
						self.hline(x_pixel+2, y_pixel+3,3,1)
						self.hline(x_pixel+5, y_pixel+1,2,1)
						self.hline(x_pixel+5, y_pixel+4,2,1)
						self.vline(x_pixel+7, y_pixel  ,4,1)
					elif self.anim_step in (1,6):
						self.rect(x_pixel,y_pixel,2,8,1)
						self.hline(x_pixel+2, y_pixel  ,2,1)
						self.hline(x_pixel+2, y_pixel+3,2,1)
						self.hline(x_pixel+4, y_pixel+1,2,1)
						self.hline(x_pixel+4, y_pixel+4,2,1)
						self.pixel(x_pixel+6, y_pixel  , 1)
						self.pixel(x_pixel+6, y_pixel+4, 1)
						self.vline(x_pixel+7, y_pixel  ,4,1)
					elif self.anim_step in (2,7):
						self.rect(x_pixel,y_pixel,2,8,1)
						self.pixel(x_pixel+2, y_pixel+0, 1)
						self.pixel(x_pixel+2, y_pixel+3, 1)
						self.hline(x_pixel+3, y_pixel+1,2,1)
						self.hline(x_pixel+3, y_pixel+4,2,1)
						self.hline(x_pixel+5, y_pixel+0,3,1)
						self.hline(x_pixel+5, y_pixel+3,3,1)
						self.vline(x_pixel+7, y_pixel+1,2,1)
					elif self.anim_step==3:
						self.rect(x_pixel,y_pixel,2,8,1)
						self.pixel(x_pixel+2, y_pixel+0, 1)
						self.pixel(x_pixel+2, y_pixel+3, 1)
						self.pixel(x_pixel+3, y_pixel+1, 1)
						self.pixel(x_pixel+3, y_pixel+4, 1)
						self.hline(x_pixel+4, y_pixel+0,4,1)
						self.hline(x_pixel+4, y_pixel+3,4,1)
						self.vline(x_pixel+7, y_pixel+1,2,1)
					elif self.anim_step in (4,8):
						self.rect(x_pixel,y_pixel,2,8,1)
						self.hline(x_pixel+2, y_pixel+0,6,1)
						self.hline(x_pixel+2, y_pixel+3,6,1)
						self.vline(x_pixel+7, y_pixel+1,2,1)
				elif (c.state!=None) and (c.state==0): # Inspected, no bomb arround
					self.pixel(x_pixel,y_pixel               , 1)
					self.pixel(x_pixel+TILE_W, y_pixel       , 1)
					self.pixel(x_pixel       , y_pixel+TILE_H, 1) # Go one pixel over the tile border
					self.pixel(x_pixel+TILE_W, y_pixel+TILE_H, 1) 
				elif (c.state!=None) and (1 <= c.state <= 8): # State in 1..8 (number of bomb around the cell)
					self.text_drawer.text( str(c.state), x_pixel+3, y_pixel+1, 1)
				elif c.mine and self.gameover:
					# self.fbtls.fill_circle(x_pixel+4,y_pixel+4,4,1) # Too slow
					self.rect(x_pixel+2, y_pixel+2,4,4,1 )
					self.hline(x_pixel,y_pixel+3,8,1)
					self.hline(x_pixel,y_pixel+4,8,1)
					self.vline(x_pixel+3,y_pixel,2,1)
					self.vline(x_pixel+4,y_pixel,2,1)
					self.vline(x_pixel+3,y_pixel+6,2,1)
					self.vline(x_pixel+4,y_pixel+6,2,1)

		# Draw the cursor (once every 2 seconds)
		if (now//500)%2 == 0: 
			self.rect( XOFF+1+(self.prel.x*TILE_W), YOFF+1+(self.prel.y*TILE_H), TILE_W, TILE_H, 1) # +3 for scrollbar)
			 
		# Draw Frame around gameboard
		self.rect(XOFF, YOFF, XTILES*TILE_W+2+3, YTILES*TILE_H+2+3, 1) # +3 for scrollbar
		self.vline(XOFF+XTILES*TILE_W+1, YOFF+1, YTILES*TILE_H+3, 1)
		self.hline(XOFF+1, YOFF+YTILES*TILE_H+1, XTILES*TILE_W+3, 1)
		#self.hline()
		
		# Draw the scroll bar position
		bar_width = int((XTILES*TILE_W)*(XTILES/self.board.width))
		bar_x     = int((self.tlc.x)/self.board.width*XTILES*TILE_W)
		self.rect( XOFF+1+bar_x, YOFF+1+YTILES*TILE_H+1, bar_width, 2, 1)
		bar_height= int((YTILES*TILE_H)*(YTILES/self.board.height))
		bar_y     = int((self.tlc.y)/self.board.height*YTILES*TILE_H)
		self.rect( XOFF+1+XTILES*TILE_W+1, YOFF+1+bar_y, 2, bar_height, 1)

		# Draw the GameOver text
		if self.gameover:
			score = "score: %i / %i" % ( len( list([mine for mine in self.board.mines if mine.state==FLAGGED_STATE]) ), len(self.board.mines) )
			score_w = self.text_drawer.font.text_width(score)
			self.fill_rect( (self.width-score_w)//2-1, 0, score_w+2, 6, 0 )
			self.text_drawer.text( score, (self.width-score_w)//2, 0, 1)
			
		self.show()

		# === cHECK wINNING ===
		if all( [ mine.state==FLAGGED_STATE for mine in self.board.mines ] ):
			self.show_winner()
			return False

		return True

	def run( self ):
		while True:
			self.show_intro()
			self.select_level()
			self.init_game()
			while self.draw_frame():
				pass			

game=Game()
game.run()		