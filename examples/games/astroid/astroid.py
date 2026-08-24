# Astroid game for Pico-Oled_boot
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

MAX_AST = const(8) # Max asteroid
SHIP_W  = const(9)
SHIP_H  = const(8)

class Rock:
	__slots__ = ("x","y","spd","w","h","on")

	def __init__(self, x=0, y=0, w=0, h=0 ):
		self.x=x   # float
		self.y=y   # float
		self.spd=0 # float
		self.w=w   # int
		self.h=h   # int
		self.on = False


class Game(OledBoot):
	def __init__( self ):
		super().__init__() # Add rotate as needed
		self.fbtls   = FBUtil( self )
		self.text_drawer = FBText( self, self.width, self.height, Font8X4() )
		self.rocks = [] # list [MAX_AST] of Rock
		self.init_game() # Initialize the variable?

	def show_intro(self):
		self.fill(0)
		self.text( "Astroid", (self.width-5*8)//2, self.height//4 )
		#self.text( "Invaders", (self.width-9*8)//2, self.height//4+10 )		
		self.text_drawer.text("UP/DOWN to dodge", 0, 64-20, 1)
		self.text_drawer.text("Just survive!", 0, 64-8, 1)
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)

	def show_score( self ):
		pass

	def show_winner( self ):
		self.fill_rect( 25, 16, 78, 36, 0 )	
		self.rect( 26, 17, 76, 34, 1 )	
		self.text( "You  Win!", 28, 21)
		self.text_drawer.text( "Score: %i" % (self.score//10), 45, 29, 1 )
		self.text_drawer.text( "Press key", 45, 39, 1 )
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)		

	def show_gameover( self ):
		self.fill_rect( 25, 16, 78, 36, 0 )	
		self.rect( 26, 17, 76, 34, 1 )	
		self.text( "GAME OVER", 28, 21)
		self.text_drawer.text( "Score: %i" % (self.score//10), 45, 29, 1 )
		self.text_drawer.text( "Press key", 45, 39, 1 )
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)		

	def init_game( self ):
		self.ship_y = self.height//2 - SHIP_H//2
		self.rocks.clear()
		for i in range( MAX_AST ):
			self.rocks.append( Rock() )
		self.score = 0
		self.last_spawn = 0
		self.last_frame = time.ticks_ms()
		self.spawn_gap = 900

		# Starts displayed on the background
		self.star_x = [20, 45, 70, 95, 110, 35, 60, 85]
		self.star_y = [8, 24, 12, 40, 55, 50, 36, 20]


  	def draw_frame( self ):
		now = time.ticks_ms()

		dir = self.dir # Only one request
		dt = time.ticks_diff(now, self.last_frame) / 30.0
		self.last_frame = now

		dir = self.dir
		if dir==UP:
			self.ship_y = max(0, self.ship_y-3)
		if dir==DOWN:
		 	self.ship_y = min(self.height-SHIP_H, self.ship_y+3)

		self.score += 1
		self.spawn_gap = max(300, 900-(self.score//100))
		# print( "spawn_gap" , self.spawn_gap, 'diff', time.ticks_diff( now, self.last_spawn ) )
		if time.ticks_diff( now, self.last_spawn ) > self.spawn_gap:
			self.last_spawn = now
			for r in self.rocks:
				if not r.on:
					r.x = self.width+4
					r.y = random.randint(2, self.height-14)
					r.w = random.randint(5, 13)
					r.h = random.randint(5, 11)
					r.spd = random.randint(18, 40)/10.0
					r.on  = True
					break

		for r in self.rocks:
			if not r.on:
				continue
			r.x -= int(r.spd * dt)
			if (r.x+r.w) < 0:
				r.on = False
				continue
			if (r.x < (2+SHIP_W)) and ((r.x+r.w)> 2) and (r.y < (self.ship_y+SHIP_H)) and ((r.y+r.h)>self.ship_y):
				self.show_gameover()
				return False
			

		# Draw Screen
		self.fill(0)
		for i in range(8):
			self.pixel( self.star_x[i], self.star_y[i], 1 )
		
		# Draw the Ship
		self.line(2, self.ship_y+4, 10, self.ship_y , 1)
		self.line(2, self.ship_y+4, 10, self.ship_y+8, 1 )
		self.line(10, self.ship_y, 10, self.ship_y+8, 1 )
		if (now % 2) == 0:
		  self.line(0, self.ship_y+3, 2, self.ship_y+4, 1)
		  self.line(0, self.ship_y+5, 2, self.ship_y+4, 1)
		else:
			self.pixel(1, self.ship_y+4, 1)

		for r in self.rocks:
			if not r.on:
				continue
			rx = int(r.x)
			ry = int(r.y)
			self.rect(rx, ry, r.w, r.h, 1)
			self.pixel(rx, ry, 1)
			self.pixel(rx+r.w-1, ry, 1)
			self.pixel(rx, ry+r.h-1, 1)
			self.pixel(rx+r.w-1, ry+r.h-1, 1)

		s = "%s"%(self.score//10)
		self.text( s, self.width-(len(s)*8)-2, 8 )
		self.show()

		wait = 33 - time.ticks_diff( time.ticks_ms(), now)
		if wait > 0:
			time.sleep_ms( wait )

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