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

display = OledBoot()
fbtls   = FBUtil( display )
text_drawer = FBText( display, display.width, display.height, Font8X4() )
random.seed( machine.ADC(machine.Pin(28)).read_u16() )

BRK_COLS = const(10)
BRK_ROWS = const(4)
BRK_BW   = const(11) # Brick Width
BRK_BH   = const( 5) # brick Height
BRK_PADW = const(20) # Pad Width
BRK_PADH = const( 3) # Pad Height

bricks    = [] # List[BRK_ROWS][BRK_COLS]
left      = 0   # Number of bricks left 
pad_x, pad_y = 0, 0 # Pad position
b_x, b_y  = 0, 0 # Ball position
v_x, v_y  = 0, 0 # Velocity (floats)
lives     = 0
score     = 0
last_frame= 0 # ms used to display the last Frame

def draw_intro():
	display.fill(0);
	display.text("BREAKOUT", (128-8*8)//2, (64-8)//3 )
	text_drawer.text("LEFT/RIGHT = paddle", 0, 64-20, 1)
	text_drawer.text("Don't drop the ball!", 0, 64-8, 1)
	display.show()
	while not display.any_key_pressed:
		time.sleep_ms(50)


def draw_score():
	pass

def draw_gameover():	
	display.fill_rect( 25, 16, 78, 36, 0 )	
	display.rect( 26, 17, 76, 34, 1 )	
	display.text( "GAME OVER", 28, 21)
	text_drawer.text( "Score: %i" % score, 45, 29, 1 )
	text_drawer.text( "Press key", 45, 39, 1 )
	display.show()
	while not display.any_key_pressed:
		time.sleep_ms(50)		


def init_level():
	global bricks, left, pad_x, pad_y, b_x, b_y, v_x, v_y, lives, score, last_frame
	bricks.clear()
	for i in range( BRK_ROWS ):
		bricks.append( [1]*BRK_COLS )

	left = BRK_ROWS * BRK_COLS
	pad_x = (display.width - BRK_PADW) // 2
	pad_y = display.height - 6
	b_x, b_y = 64, 48
	v_x, v_y = 1.7, -0.5
	last_frame = 0


def draw_frame():
	"""  display a game Frame.
	Returns True to continue Frame drawing. False to stop the game
	A frame takes about 45ms """
	global bricks, left, pad_x, pad_y, b_x, b_y, v_x, v_y, lives, score, last_frame

	dir = display.dir
	start_frame = time.ticks_ms()
	dt = last_frame  / 30.0

	if dir==LEFT:
		pad_x = max(0, pad_x-4)
	elif dir==RIGHT:
		pad_x = min(display.width - BRK_PADW, pad_x + 4)
	b_x += v_x * dt
	b_y += v_y * dt
	# print( b_x, b_y, v_x, v_y, dt, last_frame)
	if b_x <= 1:
		v_x = abs(v_x);
		b_x = 1
		#beep(600, 15);

	if b_x >= display.width - 4:
		v_x = -abs(v_x)
		b_x = display.width - 4
		# beep(600, 15);
    
	if b_y <= 1:	
		v_y = abs(v_y)
		b_y = 1
		# beep(600, 15);
    
	if (v_y > 0) and ((b_y+3) >= pad_y) and ((b_y+3) <= (pad_y+BRK_PADH+2)) and ((b_x+2) >= pad_x) and (b_x <= (pad_x+BRK_PADW)):
		v_y = -abs(v_y)
		rel = ((b_x+1) - (pad_x+BRK_PADW/2.0)) / (BRK_PADW/2.0)
		v_x = rel * 3.0
		if abs(v_x) < 0.5:
			v_x = 0.5 if v_x>=0 else -0.5
		b_y = pad_y - 3 # Push further away
		# beep(900, 20)

	if b_y > (display.height+2):
		lives -= 1
		#beep(200, 300);
		if lives <= 0: 
			draw_gameover()
			return False

		time.sleep_ms(600)
		b_x = 64
		b_y = 45
		v_x = 1.8
		v_y = -2.2
		last_frame=0
		return True
		

	_full_break = False
	for r in range(BRK_ROWS):
		if left <= 0:
			break		
		for c in range(BRK_COLS):
			if not bricks[r][c]:
				continue
			bk_x = c * (BRK_BW + 1) + 1
			bk_y = r * (BRK_BH + 1) + 1
			if ((b_x+3) >= bk_x) and (b_x <= (bk_x+BRK_BW)) and ((b_y+3) >= bk_y) and (b_y <= (bk_y+BRK_BH)):
				bricks[r][c] = 0
				left -= 1
				score += (BRK_ROWS-r)*10
				overlap_l = b_x + 3 - bk_x
				overlap_r = bk_x + BRK_BW - b_x
				overlap_t = b_y + 3 - bk_y
				overlap_b = bk_y + BRK_BH - b_y
				min_h = min(overlap_l, overlap_r)
				min_v = min(overlap_t, overlap_b)
				if min_h < min_v:
					v_x = -v_x
				else:
					v_y = -v_y
				#beep(1200 + r * 120, 25);
				
				# Exit the double FOR
				_full_break = True 
				break

		if _full_break: # Propagate the full break
			break

	if left==0 :
		display.fill(0)
		#u8g2.setFont(u8g2_font_ncenB10_tr);
		display.text( "YOU WIN!", (128-8*8)//2, display.height//3)
		text_drawer.text( "Score: %i" % score, 45, display.height//3 +8, 1 )
		text_drawer.text( "Press key", 45, display.height//3+18, 1 )
		display.show()
		while not display.any_key_pressed:
			time.sleep_ms(50)		
		return False
	
	# Draw grid
	display.fill(0)
	for r in range( BRK_ROWS ):
		for c in range( BRK_COLS):
			if not bricks[r][c]:
				continue
			bk_x = c * (BRK_BW + 1) + 1
			bk_y = r * (BRK_BH + 1) + 1
			if (r%2)==0:
				display.fill_rect(bk_x, bk_y, BRK_BW, BRK_BH, 1)
			else:
				display.rect(bk_x, bk_y, BRK_BW, BRK_BH, 1)
	#u8g2.drawRBox(padX, padY, BRK_PADW, BRK_PADH, 1);
	display.rect( pad_x, pad_y, BRK_PADW, BRK_PADH, 1 )
	#u8g2.drawDisc((int)bx + 1, (int)by + 1, 2);
	display.ellipse( int(b_x+1), int(b_y+1), 2, 2, 1 )

	display.text("%s"%score, 1, display.height-8, 1)
	for i in range( lives ):
		display.pixel( display.width-4- i*6, 60, 1 )
		display.rect( display.width-6- i*6, 61, 5, 3, 1)

	display.show()
	last_frame = time.ticks_diff( time.ticks_ms(), start_frame ) # Time to display the full Frame
	wait = 20 - last_frame
	if wait > 0:
		time.sleep_ms( wait )

	return True


# === Main Loop ===
while True:
	draw_intro()
	score = 0
	lives = 3
	while True: # User rounds
		init_level()
		while draw_frame():
			pass
		# Game over, we start a new game
		if lives==0:
			break
	draw_score()
