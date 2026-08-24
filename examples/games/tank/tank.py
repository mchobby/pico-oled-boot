# Tank game for Pico-Oled_boot
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

MAX_ENEMY_TANKS = const(3)

def constrain( value, _min, _max ):
	_r = value if value < _max else _max
	return _r if _r > _min else _min


class Tank:
	__slots__ = ("x","y","dx","dy","active","last_move")

	def __init__(self,x=0,y=0):
		self.x=x # float
		self.y=y # float
		self.dx=0 # uint
		self.dy=0 # uint
  		self.active=False # bool
  		self.last_move=0 # ms

class TankBullet:
	__slots__ = ("x","y","dx","dy","active")

	def __init__(self,x=0,y=0):
		self.x=x # float
		self.y=y # float
		self.dx=0 # uint
		self.dy=0 # uint
  		self.active=False # bool

class Game(OledBoot):
	def __init__( self ):
		super().__init__() # Add rotate as needed
		self.fbtls   = FBUtil( self )
		self.text_drawer = FBText( self, self.width, self.height, Font8X4() )
		self.player = None # a Tank
		self.pbullet = None # TankBullet
		self.enemies = [] # list [MAX_ENEMY_TANKS] of Tank
		self.ebullets = [] # list [MAX_ENEMY_TANKS] of TankBullet
		self.init_game() # Initialize the variable?

	def show_intro(self):
		self.fill(0)
		self.text( "Tank Battle", (self.width-11*8)//2, self.height//4 )
		#self.text( "Invaders", (self.width-9*8)//2, self.height//4+10 )		
		self.text_drawer.text("Joystick to move", 0, 64-20, 1)
		self.text_drawer.text("B to Fire!", 0, 64-8, 1)
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
		self.player = Tank( x=64, y=50 )
		self.player.active = True
		self.enemies.clear()
		for i in range( MAX_ENEMY_TANKS ):
			self.enemies.append( Tank() ) # Created inactive
		self.pbullet = TankBullet()
		self.ebullets.clear()
		for i in range( MAX_ENEMY_TANKS ):
			self.ebullets.append( TankBullet() ) # Inactive by default
		self.score = 0
		self.last_spawn = 0
		self.last_frame = time.ticks_ms()

  	def draw_frame( self ):
		now = time.ticks_ms()

		dir = self.dir # Only one request
		dt = time.ticks_diff(now, self.last_frame) / 30.0
		self.last_frame = now

		# Player input
		if dir==UP :
			self.player.y -= 1.5*dt
			self.player.dx = 0
			self.player.dy = -1
		elif dir==DOWN :
			self.player.y += 1.5*dt
			self.player.dx = 0
			self.player.dy = 1
		elif dir==LEFT:
			self.player.x -= 1.5*dt
			self.player.dx = -1;
			self.player.dy = 0;
		elif dir==RIGHT:
			self.player.x += 1.5*dt
			self.player.dx = 1
			self.player.dy = 0

		self.player.x = constrain( self.player.x, 0, self.width-8 )
		self.player.y = constrain( self.player.y, 0, self.height-8 )

		if (self.button_b.pressed) and not(self.pbullet.active) and ((self.player.dx!=0)or(self.player.dy!=0)):
			self.pbullet.x = self.player.x+3
			self.pbullet.y = self.player.y+3
			self.pbullet.dx = self.player.dx
			self.pbullet.dy = self.player.dy
			self.pbullet.active = True
			#beep(1200, 20);
		

		# Spawn enemies
		if time.ticks_diff(now, self.last_spawn) > 3000:
			for enemy in self.enemies:
				if not enemy.active:
					enemy.x = random.randint(0, self.width-8)
					enemy.y = 0
					enemy.dx = 0
					enemy.dy = 1
					enemy.active = True
					enemy.last_move = now
					self.last_spawn = now
					break

		# Move enemies & enemy fire
		for idx, enemy in enumerate(self.enemies):
			if not enemy.active:
				continue

			if time.ticks_diff(now, enemy.last_move) > 1000:
				tank_dir = random.randint(0, 3) # 0:UP, 1:RIGHT, 2:DOWN, 3:LEFT
				if tank_dir == 0:
					enemy.dx = 0
					enemy.dy = -1
				elif tank_dir == 1:
					enemy.dx = 1
					enemy.dy = 0
				elif tank_dir == 2:
					enemy.dx = 0
					enemy.dy = 1
				else:
					enemy.dx = -1
					enemy.dy = 0
				enemy.last_move = now

				# Enemy fire
				if not self.ebullets[idx].active:
					self.ebullets[idx].x = enemy.x+3
					self.ebullets[idx].y = enemy.y+3
					self.ebullets[idx].dx = enemy.dx;
					self.ebullets[idx].dy = enemy.dy;
					self.ebullets[idx].active = True

			enemy.x += enemy.dx * 0.8 * dt
			enemy.y += enemy.dy * 0.8 * dt
			enemy.x = constrain( enemy.x, 0, self.width-8 )
			enemy.y = constrain( enemy.y, 0, self.height-8 )
		

		# Move bullets
		if self.pbullet.active: # Player Bullet?
			self.pbullet.x += self.pbullet.dx * 3.0 * dt
			self.pbullet.y += self.pbullet.dy * 3.0 * dt
			if (self.pbullet.x<0) or (self.pbullet.x>self.width) or (self.pbullet.y<0) or (self.pbullet.y>self.height):
				self.pbullet.active = False
		for ebullet in self.ebullets:
			if ebullet.active:
				ebullet.x += ebullet.dx * 2.0 * dt
				ebullet.y += ebullet.dy * 2.0 * dt
				if (ebullet.x<0) or (ebullet.x>self.width) or (ebullet.y<0) or (ebullet.y>self.height):
					ebullet.active = False

		# Bullet collisions
		if self.pbullet.active: # Player Bullet
			for idx, enemy in enumerate(self.enemies):
				if enemy.active and (self.pbullet.x>enemy.x) and (self.pbullet.x<(enemy.x+8)) and (self.pbullet.y>enemy.y) \
					and (self.pbullet.y<(enemy.y+8)):
					enemy.active = False
					self.pbullet.active = False
					self.score += 50
					#beep(800, 40);

		for bullet in self.ebullets: # Ennemi Bullet
			if bullet.active and (bullet.x>self.player.x) and (bullet.x<(self.player.x+8)) and (bullet.y>self.player.y) \
				and (bullet.y<(self.player.y+8)) :
				self.show_gameover()
				return False

		# === Draw ===
		self.fill(0)

		# Draw Player
		self.rect( int(self.player.x), int(self.player.y), 8, 8, 1)
		if self.player.dy == -1:
			self.vline( int(self.player.x)+3, int(self.player.y)-2, 3, 1)
		elif self.player.dy == 1:
			self.vline( int(self.player.x)+3, int(self.player.y)+7, 3, 1)
		elif self.player.dx == -1:
			self.hline( int(self.player.x)-2, int(self.player.y)+3, 3, 1)
		else:
			self.hline( int(self.player.x)+7, int(self.player.y)+3, 3, 1)

		# Draw Enemies	
		for enemy in self.enemies:
			if enemy.active:
				self.fill_rect( int(enemy.x), int(enemy.y), 8, 8, 1)
				self.pixel( int(enemy.x) + 3, int(enemy.y)+3, 0)
		    
		# Draw Bullets
		if self.pbullet.active:
			self.pixel( int(self.pbullet.x), int(self.pbullet.y), 1)
		for bullet in self.ebullets:
			if bullet.active:
				self.pixel( int(bullet.x), int(bullet.y), 1)

		# Score
		self.text( "%s"%self.score, 2, 10 )
		self.show()
		wait = 25 - time.ticks_diff( time.ticks_ms(), now)
		if wait>0:
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