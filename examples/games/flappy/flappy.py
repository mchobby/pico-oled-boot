# Flappy bird clone with OLED Display 128x64 - Comments in English
# Original https://www.makerblog.at
# Adapted to Pico-Oled-Boot
#
# Hardware Requirement:
# - Pico-Oled-Boot
# - Buzzer wired to GP16
#
# Optimization:
#   To avoid floating point numbers (float), all relevant4 positions and speeds are scaled by a factor of 10 and stored as integers.
#   This improves performance and prevents rounding errors.
#
# Example:
#  - Players vertical position y = 450 is actually at 45.0 pixels on the display.
#  - A gravity of GRAVITY = 5 means a change of 0.5 px per frame.
#  - A pipe x = 350 is actually at x = 35 pixels on the display.
#
# This scaling is used in all calculations but is converted back to the actual pixel value when displayed
# (using functions like drawBitmap, drawFastHLine, etc.) by dividing x / 10.
from micropython import const
from oledboot import *
from fbutil import FBUtil
import machine, random, time
display = OledBoot()
dutil = FBUtil( display ) # Utility methods on the target FrameBuffer

PIN_BUZZER = 16

DEBUG_PRINT = False

GRAVITY = const(5)  #  gravity applied to the character each frame
JUMP_STRENGTH = const(-25) # jump acceleration when push button is pressed
PIPE_WIDTH = const(150) # SCALE_FACTOR. pipes are 15px wide on display
PIPE_GAP = const(300) # SCALE_FACTOR. gap in pipes 30px high
PIPE_SPEED = 10 # side scroll speed
PIPE_SPACING = 650 # SCALE_FACTOR. 65px default spacing between 2 pipes
MAX_PIPES = const( 3 )


# Size of player sprite
BIRD_WIDTH_PX  = const(10)
BIRD_HEIGHT_PX = const(8)

# Game variables
bird_y = 0 # vertical position of the player
velocity = 0.0 # combined vertical velocity of the player
game_over = False
score = 0
frame_counter = 0
game_over_time = 0

# GameState
STARTSCREEN = const(0)
HIGHSCORE   = const(1)
PLAYING     = const(2)

game_state = STARTSCREEN

# Data type for a pipe (x-position, height of the upper part)
class Pipe():
	__slots__ = ('x','height')

	def __init__( self ):
		self.x = 0
  		self.height = 0

# Maximum 3 pipes simultaneously
pipes = [] 
for i in range( MAX_PIPES ):
	pipes.append( Pipe() )

# Highscore
highscores = [0,0,0,0,0]
new_highscore_index = -1
highscore_time = 0
show_blink = True
last_blink_time = 0

# Framerate control
FRAME_TIME = const(40) # 40ms per frame = 25 FPS
last_frametime = time.ticks_ms()

# Graphics for player sprite
# converted from PNG with https://javl.github.io/image2cpp/

# bird, 10x8px
bitmap_bird1 = ( 0x0e, 0x00, 0x15, 0x00, 0x60, 0x80, 0x81, 0x80, 0xfc, 0xc0, 0xfb, 0x80, 0x71, 0x00, 0x1e, 0x00 )
bitmap_bird2 = ( 0x0e, 0x00, 0x15, 0x00, 0x70, 0x80, 0xf9, 0x80, 0xfc, 0xc0, 0x83, 0x80, 0x71, 0x00, 0x1e, 0x00 )

# Array of all bitmaps for convenience. (Total bytes used to store images in PROGMEM = 64)
bitmap_birds = [bitmap_bird1, bitmap_bird2]


buzzer = machine.PWM( Pin(PIN_BUZZER) )
last_buzzer_freq  = 0  # Last used frequency for the buzzer

button_fly = display.b
random.seed(0) # Use Pico Hardware Entropy Pool

# --- Setup ---
game_state = STARTSCREEN

def constrain( value, _min, _max ):
	if _min<=value<=_max:
		return value
	if value<_min:
		return _min
	return _max

# PULLUP logic: LOW means pressed
def any_key_pressed():
	if (display.a.value()==0) or (display.b.value()==0):
		return True
	return display.dir in (START,ENTER)

def generate_pipe_height():
	# generate random height of the upper pipe section,
	# leaving at least space for gap and 10px for lower part
	return random.randrange(10*10, display.height*10 - PIPE_GAP - 10*10) # SCALE_FACTOR


# ---- Reset game ---- 
def reset_game():
	global bird_y, velocity, score, game_over, pipes
	# set start position of the player to 1/5 of the screen height
	bird_y = (display.height * 10)//5 # SCALE_FACTOR
	velocity = 0
	score = 0
	game_over = False

	# create first pipe just outside the screen edge
	pipes[0].x = display.width * 10 # SCALE_FACTOR
	pipes[0].height = generate_pipe_height()
	# create pipes 2 and 3 with random variation in spacing
	for i in range( MAX_PIPES-1 ):
		pipes[i+1].x = display.width*10 + (i+1)*PIPE_SPACING + random.randrange(-20, 20)*10 # SCALE_FACTOR
		pipes[i+1].height = generate_pipe_height()
	

def find_furthest_pipe():
	#  helper function to find the pipe farthest to the right
	maxX = 0
	for pipe in pipes:
		if pipe.x > maxX:
			maxX = pipe.x

	return maxX


def move_pipes():
	# move pipes toward the player
	global score, pipes

	current_speed = PIPE_SPEED + score # pipes move faster and faster

	for pipe in pipes:
		# move pipe position left by currentSpeed
		pipe.x -= current_speed
		# if pipe leaves the left edge, immediately create a new pipe at the right edge
		if pipe.x < -PIPE_WIDTH:
			pipe.x = find_furthest_pipe() + PIPE_SPACING + random.randrange(-20, 20)*10 # place new pipe far right
			pipe.height = random.randrange(10*10, display.height*10 - PIPE_GAP - 10*10)
			score += 1


# ---- Collision detection ---- 
def check_collision():
	# collision check with a 2px smaller hitbox (Collision Forgiveness),
	global game_over, game_over_time, pipes
	# because the player is more round → avoids unfair edge hits
	for pipe in pipes:
		# check if the player overlaps horizontally with a pipe 
		if ( pipe.x < ((15+2)*10) ) and ( (pipe.x+PIPE_WIDTH) > ((15-2)*10) ):
			# check if the player hits the pipe vertically (top or bottom)
			if ( (bird_y - 2*10) < pipe.height ) or ( (bird_y + 2*10) > (pipe.height+PIPE_GAP) ):
				game_over = True
				game_over_time = time.ticks_ms()
				save_highscores(score)

	# if player below the screen bottom
	if bird_y >= (display.height*10):
		game_over = True
		game_over_time = time.ticks_ms()
		save_highscores(score)


def draw_bird():
	bird_frame = (frame_counter//5) % 2
	# x, y, bitmap, bitmap_w, bitmap_h, color
	dutil.draw_bitmap( 15 - BIRD_WIDTH_PX//2, bird_y//10 - BIRD_HEIGHT_PX//2,
                     bitmap_birds[bird_frame], BIRD_WIDTH_PX, BIRD_HEIGHT_PX, 1)



def draw_pipes():
	for pipe in pipes:
		pipeX = pipe.x // 10 #SCALE_FACTOR
		upperPipeHeight = pipe.height // 10 # SCALE_FACTOR
		gapHeight = PIPE_GAP // 10 # SCALE_FACTOR
		lowerPipeY = upperPipeHeight + gapHeight
		lowerPipeHeight = display.height - lowerPipeY
		pipeWidth = PIPE_WIDTH // 10 # SCALE_FACTOR

		# upper pipe segment (vertical)
		display.fill_rect(pipeX, 0, pipeWidth, upperPipeHeight-6, 1 )
		# pipe head top (horizontal cap)
		display.fill_rect(pipeX - 2, upperPipeHeight-6, pipeWidth+4, 6, 1 )
		# pipe head bottom (horizontal cap below gap)
		display.fill_rect(pipeX - 2, lowerPipeY, pipeWidth + 4, 6, 1)
		# lower pipe segment (vertical)
		display.fill_rect(pipeX, lowerPipeY+6, pipeWidth, lowerPipeHeight-6, 1 )


def draw_score():
	# show current score at top right of display
	display.text( str(score), 110, 2)


# ---- Show start screen ---- 
def render_start_screen():
	display.fill(0)

	display.text("Ardu Bird",30,0)
	display.text("Use B to fly",15,30)
	display.text("Press to start",10,40);
	display.show()


# ---- Show Game Over ---- 
def display_gameover():
  display.fill_rect(20, 5, display.width-40, display.height-10, 1 )
  display.rect( 19,4, display.width-40+1, display.height-10+1, 0 )
  display.rect( 22,7, display.width-40-4, display.height-10-4, 0 )
  display.text("GAME OVER", 29, 10, 0)
  display.text("Your score", 23, 20, 0)

  #sprintf(scoreBuffer, "%d", score);  // convert number to string
  s = str( score )
  display.text(s, 64-(len(s)*8//2), 40, 0)

# ---- Show Highscore list ----
def render_highscore_screen():
	global last_blink_time, show_blink
	display.fill(0)
	display.text("HIGHSCORES", 25, 2, )	

	# current achieved score should blink if in Top10, blink status changes every 100ms
	if time.ticks_diff( time.ticks_ms(), last_blink_time ) > 100:
		show_blink = not(show_blink)
		last_blink_time = time.ticks_ms()
	
	for i in range( len(highscores) ):
		if (i==new_highscore_index) and not(show_blink):
			continue
		display.text( "%i. %i" % (i+1, highscores[i]), 30, 14+(i*9) )
	display.show()

# ---- Save highscores ---- //
def save_highscores(new_score):
	global new_highscore_index, highscores
	highscores.append( new_score )
	highscores.sort(reverse=True)
	highscores = highscores[0:5] # keeps the first 5ones

	new_highscore_index = -1
	if new_score in highscores:
		new_highscore_index = highscores.index( new_score )

# ---- Draw game ---- 
def draw_game():
	display.fill(0)

	draw_bird()
 	draw_pipes()
 	draw_score()
	if game_over:
		# display overlay
		display_gameover()
	display.show()


# ---- MainLoop ---- 
while True:
	current_time = time.ticks_ms()

	# ensure that the next frame is only calculated after 40ms
	if time.ticks_diff( current_time, last_frametime) < FRAME_TIME:
		continue
	
	last_frametime = current_time
	frame_counter += 1

	if game_state==STARTSCREEN:
		render_start_screen();
		if any_key_pressed():
			reset_game() # reset variables
			game_state = PLAYING # start game

	elif game_state==PLAYING:
		if game_over:
			# after game over, automatically switch to highscore screen after 3 seconds
			if time.ticks_diff( time.ticks_ms(), game_over_time ) > 3000:
				game_state = HIGHSCORE
				highscore_time = time.ticks_ms()
			# or player presses button (1 sec pause), then start new game immediately
			if (time.ticks_diff( time.ticks_ms(), game_over_time) > 1000) and any_key_pressed():
				reset_game()
				game_state = PLAYING
		else:
			# if button pressed, add negative acceleration (upwards)
			if button_fly.value()==0 :
				velocity = JUMP_STRENGTH
			velocity += GRAVITY # apply gravity
			velocity = constrain(velocity, -50, 50) # limit velocity to prevent too fast falling or rising

			# calculate player position
			bird_y += velocity
			# if player at top (y=0), do not go off screen
			if bird_y < (BIRD_HEIGHT_PX//2)*10:
				bird_y = (BIRD_HEIGHT_PX//2)*10

			if DEBUG_PRINT:
				print("Bird_y", bird_y , "Vel: ", velocity )
				
			move_pipes()
			check_collision()

		draw_game()

	elif game_state==HIGHSCORE:
		render_highscore_screen()
		# after 8 seconds without button press, switch to start screen
		if time.ticks_diff( time.ticks_ms(), game_over_time ) > 8000:
			game_state = STARTSCREEN
		# or start new game if button pressed
		if any_key_pressed():
			reset_game();
			game_state = PLAYING
