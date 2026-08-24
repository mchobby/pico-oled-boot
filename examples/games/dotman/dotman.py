# DotMan is a pacman alike game for Pico-Oled_boot
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

PAC_SIZE   = const(12)
PAC_MAZE_W = const(10)
PAC_MAZE_H = const(5)


class Game(OledBoot):
	def __init__( self ):
		super().__init__() # Add rotate as needed
		self.fbtls   = FBUtil( self )
		self.text_drawer = FBText( self, self.width, self.height, Font8X4() )
		self.maze = [] # list of list [PAC_MAZE_H][PAC_MAZE_W] of boolean
		self.init_game() # Initialize the variable?

	def show_intro(self):
		self.fill(0)
		self.text( "DOTMAN", (self.width-5*8)//2, self.height//4 )
		#self.text( "Invaders", (self.width-9*8)//2, self.height//4+10 )		
		self.text_drawer.text("Joystick to Move", 0, 64-20, 1)
		self.text_drawer.text("eat all dots!", 0, 64-8, 1)
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
  		self.p_x = 64 # Pacman
  		self.p_y = 32
  		self.p_dx = 0
  		self.p_dy = 0
  		self.score = 0
  		self.maze.clear()
  		for y in range(PAC_MAZE_H):
  			self.maze.append( [True]*PAC_MAZE_W )
  		self.g_x = 10 # Ghost
  		self.g_y = 10
  		self.g_dir = RIGHT
  		self.g_speed_count = 0

  	def draw_frame( self ):
		start = time.ticks_ms()

		dir = self.dir # Only one request
		if dir==UP:
			self.p_dx = 0
			self.p_dy = -2
		elif dir==DOWN:
			self.p_dx = 0
			self.p_dy = 2
		elif dir==LEFT:
			self.p_dx = -2
			self.p_dy = 0
		elif dir==RIGHT:
			self.p_dx = 2
			self.p_dy = 0

		self.p_x += self.p_dx
		self.p_y += self.p_dy

		# Boundaries
		if self.p_x < 4:
		  self.p_x = 4
		if self.p_x > (self.width-4):
		  self.p_x = self.width-4
		if self.p_y < 4:
		  self.p_y = 4
		if self.p_y>(self.height-4):
		  self.p_y = self.height-4

		# Dot eating
		mx = (self.p_x * PAC_MAZE_W) // self.width;
		my = (self.p_y * PAC_MAZE_H) // self.height
		if (mx>=0) and (mx<PAC_MAZE_W) and (my>=0) and (my<PAC_MAZE_H):
			if self.maze[my][mx]:
				self.maze[my][mx] = False
				self.score += 10
				#beep(1000, 10);

		# Ghost AI (Slower)
		#  static uint8_t gSpeedCount = 0;
		self.g_speed_count += 1
		if (self.g_speed_count%2)==0:
			if self.g_x < self.p_x:
				self.g_x += 1
			elif self.g_x>self.p_x:
				self.g_x -= 1
			if self.g_y<self.p_y:
				self.g_y += 1
			elif self.g_y>self.p_y:
				self.g_y -= 1
		
		# Collision
		if (abs(self.p_x-self.g_x)<6) and (abs(self.p_y-self.g_y)<6):
			self.show_gameover()
		  	return False

		# Win check
		win = True
		_all_break = False
		for y in range(PAC_MAZE_H):
			for x in range(PAC_MAZE_W):
				if self.maze[y][x]:
					win = False
					_all_break = True
					break
			if _all_break:
				break

		if win:
			self.show_winner()
			return False

		# Draw the Game Board
		self.fill(0)
		# Draw dots
		for y in range(PAC_MAZE_H):
			for x in range(PAC_MAZE_W):
				if self.maze[y][x]:
					dx = ((x*self.width)//PAC_MAZE_W) + (self.width// (PAC_MAZE_W*2))
					dy = ((y*self.height)//PAC_MAZE_H) + (self.height// (PAC_MAZE_H*2))
					self.pixel(dx, dy, 1)

		# Draw Pac
		self.ellipse( self.p_x, self.p_y, 4, 4, 1 )
		# Draw Ghost
		self.fill_rect( self.g_x-3, self.g_y-3, 7, 7, 1)
		self.pixel( self.g_x-1, self.g_y-1, 0 )
		self.pixel( self.g_x+1, self.g_y-1, 0 )

		self.text( "%s"%self.score, 63, 1, 1 )
		self.show()
		
		wait = 30 - time.ticks_diff( time.ticks_ms(), - start)
		if wait>0:
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