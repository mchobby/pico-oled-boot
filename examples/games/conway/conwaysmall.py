# The Conway Game of life
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from micropython import const
from oledboot import *
import machine, random, time, framebuf
display = OledBoot()

# Conway Life game inside a small screen section
CONWAY_WIDTH  = 30
CONWAY_HEIGHT = 30
# Top-Left corner position on the screen
CONWAY_LEFT = (display.width-CONWAY_WIDTH)//2
CONWAY_TOP  = (display.height-CONWAY_HEIGHT)//2

SHOW_PROGRESS = (CONWAY_WIDTH * CONWAY_HEIGHT) > 900
# Display have its current FrameBuffer (current status for the Game of Live)
# Let's have a second frame buffer (128x64 px) for the next state for the game
# for framebuf.MONO_HMSB  ==> bytes_per_line = (CONWAY_WIDTH//8)+(0 if CONWAY_WIDTH%8==0 else 1)
# for framebuf.MONO_VLSB =+> 
bytes_per_column = (CONWAY_HEIGHT//8)+(0 if CONWAY_HEIGHT%8==0 else 1)
buf = bytearray( CONWAY_WIDTH*bytes_per_column )
next_state = framebuf.FrameBuffer( buf, CONWAY_WIDTH, CONWAY_HEIGHT, framebuf.MONO_VLSB ) # (framebuf.MONO_HMSB if display.rotate90 else


def map(value, istart, istop, ostart, ostop):
	# map value between [istart-istop] input interval to its [ostart-ostop] output interval
	# float compatible. Use int() to remove decimal part
	return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))


def seed_game( display ):
	# randomise a game
	global buf, next_state
	for i in range(len(buf)):
		buf[i] = random.randint(0,255)
	display.blit( next_state, CONWAY_LEFT, CONWAY_TOP ) # x, y

def compute_cell( display, xtop,ytop,w,h, x, y ):
	""" x, y are absolute position of the pixel in the screen) """
	n = 0 # Neightbors 
	for _x in range(3):
		for _y in range( 3 ):
			# skip the current cell
			if (_x==1) and (_y==1):
				continue
			xx = x-1+_x
			yy = y-1+_y
			# limit x value
			if xx<xtop:
				xx=xtop+w+(xx-xtop)
			elif xx>=(xtop+w):
				xx = xx - w
			# limit y value 
			if yy<ytop:
				yy=ytop+h+(yy-ytop)
			elif yy>=(ytop+h):
				yy = yy - h
			# count neighbors
			if display.pixel(xx,yy):
				n+=1	
	if display.pixel(x,y)==1: # Alive cell can stay alive when only 2 or 3 neighbors
		return 2<=n<=3 
	else: # Dead cell can get alive if it have 3 neighbors
		return n==3



random.seed( machine.ADC(machine.Pin(28)).read_u16() )
seed_game( display )
display.show()
while True:
	# calculate next iteration
	# randomise a game
	for x in range( CONWAY_WIDTH ):
		# Display Progress on the current screen
		if SHOW_PROGRESS  and (x%8==0):
			progress_width = int( map( x, 0, CONWAY_WIDTH, 0, display.width ) )
			display.fill_rect( 0,0, progress_width, 4, 1 )
			display.show()

		for y in range( CONWAY_HEIGHT ):			
			next_state.pixel(x,y, compute_cell(display, CONWAY_LEFT, CONWAY_TOP, CONWAY_WIDTH, CONWAY_HEIGHT, CONWAY_LEFT+x, CONWAY_TOP+y) )
	# draw new state
	display.blit( next_state, CONWAY_LEFT, CONWAY_TOP ) # x, y
	# erase progress
	display.fill_rect( 0,0, display.width, 4, 0 )
	display.show()