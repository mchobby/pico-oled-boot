# SpaceInvaders game for Pico-Oled_boot
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

INV_COLS = const(8) # Col & Rows of invaders
INV_ROWS = const(3) 
INV_W    = const(7) # Width & Height of an Invader
INV_H    = const(5)
INV_BULLETS = const(3)

class Bullet:
	__slots__ = ('x','y','on') # Float, Float, boolean

	def __init__( self, x=0, y=0 ):
		self.x=x
		self.y=y
		self.on = False


class Game(OledBoot):
	def __init__( self ):
		super().__init__() # Add rotate as needed
		self.fbtls   = FBUtil( self )
		self.text_drawer = FBText( self, self.width, self.height, Font8X4() )
		self.inv = [] # List of list [INV_ROWS][INV_COLS]
		self.pb  = [] # player bullet : list of Bullet[INV_BULLETS]
		self.eb  = [] # ennemy bullet : list of Bullet[INV_BULLETS]
		self.init_game() # Initialize the variable?

	def show_intro(self):
		self.fill(0)
		self.text( "Space", (self.width-5*8)//2, self.height//4 )
		self.text( "Invaders", (self.width-9*8)//2, self.height//4+10 )		
		self.text_drawer.text("L/R = Move (Auto-fire)", 0, 64-20, 1)
		self.text_drawer.text("Destroy them all!", 0, 64-8, 1)
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)

	def show_score( self ):
		pass

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
		self.inv.clear()
		for i in range( INV_ROWS ):
			self.inv.append( [True]*INV_COLS )
		self.left = INV_ROWS * INV_COLS # Invaders left
		self.grid_x = 4
		self.grid_y = 4
		self.grid_dx = 1
		self.last_inv_move = 0 
		self.inv_speed = 500
		self.ship_x = self.width//2 - 4
		self.ship_y = self.height - 10
		self.pb.clear()
		self.eb.clear()
		for i in range(INV_BULLETS):
			self.pb.append( Bullet() ) # player bullet
			self.eb.append( Bullet() ) # ennemy bullet
		self.last_shoot = 0
		self.last_enemy_shoot = 0
		self.score = 0
		self.wave  = 1
		self.last_frame = time.ticks_ms()
		self.anim_frame = False



	def draw_frame( self ):
		""" Return True to continue the frame drawing """	
		now = time.ticks_ms()
		dt = (now-self.last_frame)/30.0
		self.last_frame = now
		self.anim_frame = (now//300)%2

		dir = self.dir # Only one request
		if dir==LEFT:
			self.ship_x = max(0, self.ship_x-3)
		if dir==RIGHT:
			self.ship_x = min(self.width-10, self.ship_x+3)
		# Autofire
		if time.ticks_diff(now,self.last_shoot) > 450:
			for b in self.pb:
				if not b.on:
					b.x = self.ship_x+4
					b.y = self.ship_y-1
					b.on = True
					#beep(1500, 15);
					break
			self.last_shoot = now
		
		# Player Bullet
		for b in self.pb:
			if not b.on:
				continue
			b.y -= 4.0 * dt
			if b.y < 0 :
				b.on = False
				continue
			bc = (int(b.x)-self.grid_x) // (INV_W+2)
			br = (int(b.y)-self.grid_y) // (INV_H+3)
			if (bc>=0) and (bc<INV_COLS) and (br>=0) and (br<INV_ROWS) and self.inv[br][bc]:
				ix = self.grid_x + bc * (INV_W + 2)
				iy = self.grid_y + br * (INV_H + 3)
				if (b.x>=ix) and (b.x<=(ix+INV_W)) and (b.y>=iy) and (b.y<=(iy+INV_H)):
			  		self.inv[br][bc] = False
			  		self.left -= 1
			  		self.score += (INV_ROWS-br) * 10
			  		b.on = False
			  		#beep(800 - br * 100, 40);

		if (self.left>0) and ( time.ticks_diff(now,self.last_enemy_shoot) > max(400, 1200-self.score*2) ):
			self.last_enemy_shoot = now
			tries = 20
			while tries>0:
				c = random.randint(0, INV_COLS-1)
				# for (int r = INV_ROWS - 1; r >= 0; r--) {
				_all_break = False
				for r in range( INV_ROWS-1, -1, -1 ):
					# print( 'r', r, 'c', c)
					if self.inv[r][c]:
						for b in self.eb:
							if not b.on:
								b.x = self.grid_x + c * (INV_W+2) + INV_W//2
								b.y = self.grid_y + r * (INV_H+3) + INV_H
								b.on = True
								# Stop the both loop
								_all_break = True
								break
					if _all_break:
						break
				if _all_break:
					break
				tries -= 1			

		

		for b in self.eb:
			if not b.on:
				continue
			b.y += 3.0 * dt;
			if b.y > self.height:
				b.on = False
				continue
			if (b.x>=self.ship_x) and (b.x<=(self.ship_x+10)) and (b.y>=self.ship_y) and (b.y<=(self.ship_y+7)):
			  self.show_gameover()
			  return False

		if time.ticks_diff(now, self.last_inv_move) > self.inv_speed:
			self.last_inv_move = now
			self.grid_x += self.grid_dx
			left_c = INV_COLS
			right_c = -1
			for r in range( INV_ROWS ):
				for c in range( INV_COLS ):
					if self.inv[r][c]:
						left_c = min(left_c, c)
						right_c = max(right_c, c)
			if ( (self.grid_x+right_c*(INV_W+2)+INV_W)>=(self.width-2) ) or ( (self.grid_x+left_c*(INV_W+2))<=2 ):
				self.grid_dx = -1*self.grid_dx
				self.grid_y += 3
			if (self.grid_y+INV_ROWS*(INV_H+3) )>=(self.ship_y-2):
				self.show_gameOver()
				return False

		if self.left==0:
			self.wave += 1
			self.inv_speed = max(80, self.inv_speed - 60)
			for r in range( INV_ROWS ):
				for c in range( INV_COLS ):
					inv[r][c] = True
			self.left = INV_ROWS*INV_COLS
			self.grid_x = 4
			self.grid_y = 4
			self.grid_dx = 1
			#beep(1760, 100);
			#delay(110);
			#beep(2093, 200);
			#delay(400);
			time.sleep_ms(500)

		# Draw screen
		self.fill(0)
		for r in range(INV_ROWS):
			for c in range(INV_COLS):
				if not self.inv[r][c]:
					continue
				ix = int( self.grid_x+c*(INV_W+2) )
				iy = int( self.grid_y+r*(INV_H+3) )
				if r==0:
					self.fill_rect(ix+1, iy, 5, 2, 1)
					self.fill_rect(ix, iy+2, 7, 2, 1)
					if self.anim_frame:
						self.pixel(ix, iy+4, 1)
						self.pixel(ix+6, iy+4, 1)
					else:
						self.pixel(ix+1, iy+4, 1)
						self.pixel(ix+5, iy+4, 1)
				elif r==1:
					self.fill_rect(ix+1, iy+1, 5, 3, 1);
					self.pixel(ix + 1, iy);
					self.pixel(ix + 5, iy);
					if self.anim_frame:
						self.pixel(ix, iy+2)
						self.pixel(ix+6, iy+2)
					else:
						self.pixel(ix  , iy+3, 1)
						self.pixel(ix+6, iy+3, 1)					
				else:
					self.fill_rect(ix+2, iy, 3, 4, 1)
					self.pixel(ix+1, iy+1, 1)
					self.pixel(ix+5, iy+1, 1)
					if self.anim_frame:
						self.pixel(ix, iy+4, 1)
						self.pixel(ix+3, iy+4, 1)
						self.pixel(ix+6, iy+4, 1)
					else:
						self.pixel(ix+1, iy+4, 1)
						self.pixel(ix+5, iy+4, 1)
				    
		self.fill_rect(self.ship_x+3, self.ship_y  , 4, 2, 1)
		self.fill_rect(self.ship_x+1, self.ship_y+2, 8, 3, 1)
		self.fill_rect(self.ship_x  , self.ship_y+4, 10, 3, 1)
		for b in self.pb:
			if b.on:
				self.fill_rect( int(b.x), int(b.y), 1, 4, 1)
		for b in self.eb:
			if b.on:
				self.pixel( int(b.x), int(b.y), 1)
				self.pixel( int(b.x), int(b.y+2), 1)
	
		self.hline(0, self.height-1, self.width, 1 )
		self.text( "%s"%self.score, 1, 8, 1 )
		self.text( "W%s"%self.wave, self.width-18, 8, 1)
		self.show()
		
		wait = 20 - time.ticks_diff( time.ticks_ms(), now)
		if wait > 0:
		  	time.sleep_ms(wait)
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