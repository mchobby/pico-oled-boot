# Snake game for Pico-Oled_boot
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
# Adapted from DIY-Handled-Arduino-Game-Console for Arduino by VishnumKer
# see reference at https://github.com/Circuit-Digest/DIY-Handheld-Arduino-Game-Console
#
from micropython import const
from oledboot import *
from fbutil import FBUtil
from fbtext import *
from font8x4 import Font8X4
import machine, random, time, framebuf

random.seed( machine.ADC(machine.Pin(28)).read_u16() )

# Snake constants
SN_COLS   = const(21) # grid width  (each cell = 6 px)
SN_ROWS   = const(10) # grid height (each cell = 6 px)
SN_SZ     = const( 6)
SN_OFFX   = const( 1) # Playfield offset (for rendering)
SN_OFFY   = const( 3) # Playfield offset (for rendering)
SN_MAXLEN = const(80)

class Game(OledBoot):
	def __init__( self ):
		super().__init__() # Add rotate as needed
		self.fbtls   = FBUtil( self )
		self.text_drawer = FBText( self, self.width, self.height, Font8X4() )
		self.sx = [] # list [SN_MAXLEN] of int X coordinate 
		self.sy = [] # list [SN_MAXLEN] of int y coordinate 
		self.init_game() # Initialize the variable?

	def show_intro(self):
		self.fill(0)
		self.text( "Snake", (self.width-5*8)//2, self.height//4 )
		#self.text( "Invaders", (self.width-9*8)//2, self.height//4+10 )		
		self.text_drawer.text("Joystick to move", 0, 64-20, 1)
		self.text_drawer.text("Eat to grow!", 0, 64-8, 1)
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)

	def show_score( self ):
		pass

	def show_winner( self ):
		self.fill_rect( 25, 16, 78, 36, 0 )	
		self.rect( 26, 17, 76, 34, 1 )	
		self.text( "You  Win!", 28, 21)
		self.text_drawer.text( "Score: %i" % self.score, 45, 29, 1 )
		self.text_drawer.text( "Press key", 45, 39, 1 )
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)		

	def show_gameover( self ):
		self.fill_rect( 25, 16, 78, 36, 0 )	
		self.rect( 26, 17, 76, 34, 1 )	
		self.text( "GAME OVER", 28, 21)
		self.text_drawer.text( "Score: %i" % self.score, 45, 29, 1 )
		self.text_drawer.text( "Press key", 45, 39, 1 )
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)		

	def init_game( self ):
		# Snake position
		self.sx.clear()
		self.sy.clear()
		for idx in range(SN_MAXLEN):
			self.sx.append(0)
			self.sy.append(0)
		self.dx = 1 
		self.dy = 0
		self.next_dx = 1 # Buffer for next direction
		self.next_dy = 0 # Buffer for next direction
		self.fx  = 0 # Food coord
		self.fy  = 0
		self.spd = 210 # ms per step
		self.score = 0
		# Place the Snake 
		# last entry is 0 to drag a clear cell at snake's tail
		self.slen = 4 # Snake: Data Length
		for i in range(self.slen-1): # 0..3 
			self.sx[i] = self.slen-1-i # numbered from 3 down to 0
			self.sy[i] = SN_ROWS // 2
		
		self.place_food()		
		self.last_move  = time.ticks_ms() 


	def place_food( self ):
		# Place food avoiding snake body
		while True:
			found = True
			self.fx = random.randint(0, SN_COLS-1)
			self.fy = random.randint(0, SN_ROWS-1)
			for idx in range( self.slen ):
				if (self.sx[idx]==self.fx) and (self.sy[idx]==self.fy):
					found = False
					break

			if found:
				return


  	def draw_frame( self ):
		now = time.ticks_ms()
		dir = self.dir # Only one request

		# Validate against current direction (dx, dy) to prevent U-turn
		if (dir==UP) and (self.dy==0):
			self.next_dx = 0
			self.next_dy = -1
		if (dir==DOWN) and (self.dy==0):
			self.next_dx = 0
			self.next_dy = 1
		if (dir==LEFT) and (self.dx==0):
			self.next_dx = -1
			self.next_dy = 0
		if (dir==RIGHT) and (self.dx==0):
			self.next_dx = 1
			self.next_dy = 0

		if time.ticks_diff(now, self.last_move) < self.spd:	
			time.sleep_ms(8)
			return True
		self.last_move = now

		# Apply buffered direction
		self.dx = self.next_dx;
		self.dy = self.next_dy;

		# Next head position (wrap at borders)
		nx = (self.sx[0]+self.dx+SN_COLS) % SN_COLS
		ny = (self.sy[0]+self.dy+SN_ROWS) % SN_ROWS

		# Self-collision check
		#print( "nx, ny", nx, ny)
		#print( "-".join([ "(%s,%s)" % (self.sx[i],self.sy[i]) for i in range(self.slen)]) )
		
		for i in range( self.slen ):
			if (self.sx[i]==nx) and (self.sy[i]==ny):
				self.show_gameover()
				return False
		  
		# Shift body
		for i in range( self.slen-1, -1, -1 ):
			self.sx[i] = self.sx[i-1]
			self.sy[i] = self.sy[i-1]
		# Head is at new position
		self.sx[0] = nx
		self.sy[0] = ny

		# Eat food?
		if (nx==self.fx) and (ny==self.fy):
			self.score += 1
			if self.slen < SN_MAXLEN:
				self.slen += 1
			self.spd = max(70, self.spd-7)
			#beep(1400, 35);
			self.place_food()

		# === Draw ===
		self.fill(0)
		ox = SN_OFFX 
		oy = SN_OFFY
		
		# Playfield border
		self.rect(ox-1, oy-1, SN_COLS*SN_SZ+2, SN_ROWS*SN_SZ+2, 1)

		# Snake
		for i in range(self.slen):
			px = ox + self.sx[i]*SN_SZ
			py = oy + self.sy[i]*SN_SZ
			if i==0: # head
				self.fill_rect( px, py, SN_SZ, SN_SZ, 1) # solid head
			else:
				self.rect(px+1, py+1, SN_SZ-2, SN_SZ-2, 1) # hollow body

		# Food (small filled square)
		self.fill_rect(ox+self.fx*SN_SZ+1, oy+self.fy*SN_SZ+1, SN_SZ-2, SN_SZ-2, 1)

		# Score panel (right of grid)
		self.fill_rect( self.width//2-25, 0, 50, 4, 0 )
		s = "%s" % self.score
		self.text( s, (self.width-len(s)*8)//2, 0, 1 )
		self.show()
		return True

	def run( self ):
		while True:
			self.show_intro()
			self.init_game()
			while self.draw_frame():
				pass
			self.show_gameover()
			self.show_score()

game=Game()
game.run()     