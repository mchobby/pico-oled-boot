# Breakout game for Pico-Oled_boot
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

GRAVITY    = 0.6
JUMP_FORCE = -6.5
DINO_X     = const(15)
GROUND_Y   = const(58)

random.seed( machine.ADC(machine.Pin(28)).read_u16() )

CACTUS_SMALL = const(0)
CACTUS_LARGE = const(1)
BIRD         = const(2)

DINO_W = const( 10 ) # Dino Sizing
DINO_H = const( 12 )

class Game(OledBoot):
	def __init__( self ):
		super().__init__() # Add rotate as needed
		self.fbtls   = FBUtil( self )
		self.text_drawer = FBText( self, self.width, self.height, Font8X4() )
		self.init_game() # Initialize the variable?

	def show_intro(self):
		self.fill(0)
		self.text( "DINO RUN", (self.width-8*8)//2, self.height//3 )		
		self.text_drawer.text("PRESS ANY BUTTON", 0, 64-20, 1)
		self.text_drawer.text("Avoid obstacles!", 0, 64-8, 1)
		self.show()
		while not self.any_key_pressed:
			time.sleep_ms(50)

	def show_score( self ):
		pass

	def show_gameover( self ):
		pass # use score

	def init_game( self ):
		self.dino_y = GROUND_Y - 12
		self.vel_y = 0    # velocity
		self.is_jumping = False
		self.obs_x = 130  # Obstacle (float)
		self.obs_type = 0 # 0: Small cactus, 1: Large cactus, 2: Bird
		self.obs_speed = 3.5
		self.score = 0
		self.last_frame = time.ticks_ms()

	def run( self ):
		while True:
			self.show_intro()
			self.init_game()
			while self.draw_frame():
				pass
			self.show_gameover()
			self.show_score()

	def draw_frame( self ):
		""" Return True to continue the frame drawing """
		now = time.ticks_ms()
		dt = time.ticks_diff(now, self.last_frame) / 30.0
		if dt > 2.0:
			dt = 2.0
		self.last_frame = now

		# Jump logic
		# Jump logic (Any button except A & B)
		any_btn = self.any_key_pressed
		if any_btn and not(self.is_jumping):
			self.vel_y = JUMP_FORCE
			self.is_jumping = True
			#beep(1000, 20);
		
		self.vel_y += GRAVITY * dt
		self.dino_y += self.vel_y * dt

		if self.dino_y >= (GROUND_Y-12):
			self.dino_y = GROUND_Y-12
			self.vel_y = 0
			self.is_jumping = False

		# Obstacle logic
		self.obs_x -= self.obs_speed * dt
		if self.obs_x < -20:
			self.obs_x = 130 + random.randint(0, 50)
			self.obs_type = random.randint(0, 3)
			self.score += 1
			self.obs_speed += 0.05
			#if (score % 5) == 0:
			#	beep(1500, 30)

		# Collision detection
		obs_w, obs_h, obs_y = 0,0,0 # Obstacle

		if self.obs_type == CACTUS_SMALL:
			obs_w = 6
			obs_h = 10
			obs_y = GROUND_Y-10
		elif self.obs_type == CACTUS_LARGE:
			obs_w = 10
			obs_h = 14
			obs_y = GROUND_Y-14
		else: # BIRD
			obs_w = 8
			obs_h = 6
			obs_y = GROUND_Y-25

		if (DINO_X < (self.obs_x+obs_w)) and ((DINO_X+DINO_W) > self.obs_x) and (self.dino_y < (obs_y+obs_h)) and ((self.dino_y+DINO_H) > obs_y):
			return False

		# === Draw ===
		self.fill( 0 )

		# Ground
		self.hline(0, GROUND_Y, self.width, 1)
		for i in range( 0, self.width, 10 ):
			self.pixel( i+((now//50) % 10), GROUND_Y+2, 1)

		# Dino
		self.rect( DINO_X  , int(self.dino_y), 10, 12, 1 )
		self.rect( DINO_X+7, int(self.dino_y+2), 2, 2, 1 ) # Eye
		if not self.is_jumping:
			if ((now // 100) % 2) == 0:
				self.rect( DINO_X+2, int(self.dino_y)+12, 2, 2, 1)
			else:
				self.rect( DINO_X+6, int(self.dino_y)+12, 2, 2, 1)

		# Obstacles
		if self.obs_type==CACTUS_SMALL: 
			self.rect( int(self.obs_x)+2 , int(obs_y), 2, 10, 1)
			self.pixel(int(self.obs_x)  , int(obs_y)+2, 1)
			self.pixel(int(self.obs_x)+4, int(obs_y)+1, 1)
		elif self.obs_type==CACTUS_LARGE:
			self.rect(int(self.obs_x)+3, int(obs_y), 4, 14, 1)
			self.rect(int(self.obs_x)  , int(obs_y)+4, 2, 6, 1)
			self.rect(int(self.obs_x)+8, int(obs_y)+3, 2, 7, 1)
		else: # BIRD
			if (self.obs_x > -10) and (self.obs_x < (self.width+10)):
				self.rect( int(self.obs_x), int(obs_y), 8, 4, 1)
				if (now//150) % 2 == 0:
					self.line(int(self.obs_x), int(obs_y), int(self.obs_x)-4, int(obs_y)-2, 1)
				else:
					self.line(int(self.obs_x), int(obs_y)+4, int(self.obs_x)-4, int(obs_y)+6, 1)

		# Score
		self.text( "%s"%self.score, 100, 10, 1 )

		self.show()
		wait = 20 - time.ticks_diff( time.ticks_ms(), now )
		if wait > 0:
			time.sleep_ms( wait )

		return True

game = Game()
game.run()