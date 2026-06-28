# Memory Game with OLED Display 128x64 - Comments in English
# Adapted to Pico-Oled-Boot
#
# Hardware Requirement:
# - Pico-Oled-Boot
# - Buzzer wired to GP16
#
from micropython import const
from oledboot import *
from fbutil import FBUtil
from fbtext import FBText
from font8x4 import Font8X4
from icontls import draw_icon
import machine, random, time
display = OledBoot()
dutil = FBUtil( display ) # Utility methods on the target FrameBuffer
dtext = FBText( display, display.width, display.height, Font8X4() )

random.seed(0) # Use Pico Hardware Entropy Pool

# --- BITMAP ---

CARD_W = 6
CARDS = [b'\xfc\xfc\xcc\xcc\xcc\xcc', b'\xfc\xfc\x00\x00\xfc\xfc', b'\xcc\xcc\x00\x00\xcc\xcc',
 b'\xc0\xc0\xc0\xc0\xfc\xfc', b'\x00\x00\xfc\xfc\x00\x00', b'\xfc\xfc\xcc\xcc00',
 b'\xfc\xfc\xcc\xcc\xfc\xfc', b'\xc0\xc0\xcc\xcc\xc0\xc0', b'\xfc\xfc\xcc\xcc\x00\x00',
 b'\xfc\xfc\xfc\xfc\x00\x00\x00\x00', b'\xc0\xc000\x0c\x0c', b'\xcc\xcc\xfc\xfc\xcc\xcc',
 b'\xfc\xfc\x0c\x0c\xcc\xcc', b'\x0c\x0c\xcc\xcc\xc0\xc0', b'<<00\xf0\xf0', b'\x94\xd8\xfc0\x18\x1c',
 b'\xfc\xfc0000', b'\xfc\xfc\x0c\x0c<<', b'00\xfc\xfc\x00\x00', b'\xf0\xf000<<', b'00\xfc\xfc00',
 b'\x0c\x0c\x0c\x0c\xfc\xfc', b'000000', b'\x1c\x1c\x1c\xe0\xe0\xe0', b'\x00\x0000\x00\x00',
 b'\x80\xc0\xe0\xf0\xf8\xfc', b'\xcc\xcc\xcc\xcc\xcc\xcc', b'\xcc\xcc\x00\x0000']

CARD_BACK = (0b01010100,0b10101000,0b01010100,0b10101000,0b01010100,0b10101000)

# --- ICONS ---

SMILE_ICO = [16, 0b0000000000000000, 0b0000000000000000, 0b0000111111110000, 0b0001100000011000, 0b0011000000001100, 
	0b0010011001100100, 0b0010011001100100, 0b0010000000000100, 0b0010111111110100, 0b0010111111110100, 0b0010011111100100,
	0b0011001111001100, 0b0001100000011000, 0b0000111111110000, 0b0000000000000000, 0b0000000000000000 ]

THUMB_LOW_ICO = [16, 0b0000000000000000, 0b0000000000000000, 0b0000000000000000, 0b0011111111110000, 0b0010011000010000, 
	0b0010010000011000, 0b0010010000001000, 0b0010010000001100, 0b0010010000000100, 0b0010010000000100, 0b0010011001111100, 
	0b0011111000100000, 0b0000001100100000, 0b0000000110100000, 0b0000000011100000, 0b0000000000000000 ]

HOURGLASSES_ICO = [
	[16, 0b0011111111111000, 0b0010000000001000, 0b0011111111111000, 0b0001010001010000, 0b0001010001010000, 0b0001010001010000, 
		 0b0001101010110000, 0b0000110101100000, 0b0001101010110000, 0b0001011111010000, 0b0001011011010000, 0b0001011111010000,
		 0b0011111111111000, 0b0010000000001000, 0b0011111111111000, 0b0000000000000000 ],
	[16, 0b0011111111111000, 0b0010000000001000, 0b0011111111111000, 0b0001011111010000, 0b0001011011010000, 0b0001010001010000,
		 0b0001101010110000, 0b0000110101100000, 0b0001101110110000, 0b0001011011010000, 0b0001010001010000, 0b0001000000010000,
		 0b0011111111111000, 0b0010000000001000, 0b0011111111111000, 0b0000000000000000 ],
	[16, 0b0011111111111000, 0b0010000000001000, 0b0011111111111000, 0b0001010001010000, 0b0001010001010000, 0b0001011011010000, 
		 0b0001101110110000, 0b0000110101100000, 0b0001101010110000, 0b0001010001010000, 0b0001000000010000, 0b0001000000010000,
		 0b0011111111111000, 0b0010000000001000, 0b0011111111111000, 0b0000000000000000 ]
	]


PANEL_WIDTH = 6*11 # 6 card of 10px + 1px spacing
CENTER_WIDTH = 26

# Game STATE
INTRO    = const(0)
PLAYING  = const(1) 
SCORE    = const(2) # Show score
HIGHSCORE= const(3)

# Playing Game STEPS
STEP_SHUFFLE = const(0) # Shuffle the Left & Right cards
STEP_LEFT    = const(1) # Playing: left selection
STEP_RIGHT   = const(2) # Playing: right card selection
STEP_CHECK   = const(3) # Check selected card concordance (before GO LEFT again)

class State:
	# Store bumeric state & its time
	def __init__( self, initial_state ):
		self._state = initial_state
		self.state_time = time.ticks_ms()

	@property
	def value(self):
		return self._state
	
	@value.setter
	def value(self, new_value ):
		self._state = new_value
		self.state_time = time.ticks_ms()

	@property
	def elapsed( self ):
		# Elapse time (ms) since last state change
		return time.ticks_diff( time.ticks_ms(), self.state_time )


class GameProps:
	# Store the game properties
	def __init__( self ):
		self.state = State( INTRO )
		self.step = State( STEP_SHUFFLE )
		self.cards = {}
		self.cards[STEP_LEFT] = [] # shuffled collection of cards image for Left Panel
		self.cards[STEP_RIGHT]= [] # shuffled collection of cards image
		self.discloses = {}
		self.discloses[STEP_LEFT] = [] # Left card that are disclosed
		self.discloses[STEP_RIGHT]= [] # right card that are disclosed
		self.selected = {} # Which card have been selected on LEFT & RIGHT Panel
		self.selected[STEP_LEFT] = None # Left card selected by user
		self.selected[STEP_RIGHT]= None # right card selected by user
		
		self.cursor_index = None # Current cursor position (index) in the collection of card
		self.cursor_blink = State( False )

		self.last_dir = State( 0 ) # Last state readed on the joystick (see thread)

		self.start_time = None

	def init_step( self, new_step ):
		# We do start a playing a Left or a right step
		# So initialize data related to playing a Left or Eight step
		assert self.state.value==PLAYING
		self.step.value = new_step
		self.cursor_index = self.find_first_card( new_step )
		if new_step==STEP_LEFT:
			self.selected[STEP_LEFT]=None
			self.selected[STEP_RIGHT]=None


	def update_input( self ):
		# Check for user input
		global display
		# Check if it is time to update the input.
		# Return True when the value had changed
		if game.last_dir.elapsed<50:
			return
		_d = display.dir		
		_r = _d!=self.last_dir.value
		self.last_dir.value = _d
		return _r


	def find_first_card( self, current_step ):
		# Find the first card that could be returned within the collection of card
		if not(current_step in self.discloses):
			return None
		_disclose = self.discloses[current_step]
		for idx in range( len(_disclose) ):
			if _disclose[idx]==False:
				return idx
		return None

	def shuffle_cards( self ):
		# prepare the set of LEFT and RIGHT cards 
		self.cards[STEP_LEFT].clear() # shuffled index of card 
		self.cards[STEP_RIGHT].clear() # shuffled index of card 
		self.discloses[STEP_LEFT].clear() # Left card that are disclosed
		self.discloses[STEP_RIGHT].clear() # right card that are disclosed
		for i in range( len(CARDS) ):
			self.discloses[STEP_LEFT].append( False )
			self.discloses[STEP_RIGHT].append( False )
		for left_right in (self.cards[STEP_LEFT],self.cards[STEP_RIGHT]):
			# Prepare a list
			_temp = []
			for i in range( len(CARDS) ):
				_temp.append( i )
			# Random remove from _list 
			while len(_temp)>1:
				idx=random.randrange(len(_temp))
				left_right.append( CARDS[_temp[idx]] )
				del( _temp[idx] )
			# Add the last one
			left_right.append( CARDS[_temp[0]] )

			#print( left_right )
			#print( len(left_right) )


game = GameProps()



def draw_cards( cards, disclose_list, x_from, y_from, draw_left ):
	x_counter=0
	y_counter=0
	x_offset =0
	for idx,card in enumerate(cards):
		if idx>=18:
			x_offset = 0 if draw_left else 1
		display.rect( x_from+(x_offset+x_counter)*11, y_from+y_counter*11, 10, 10, 1 )
		display.pixel( x_from+(x_offset+x_counter)*11, y_from+y_counter*11, 0 )
		display.pixel( x_from+(x_offset+x_counter)*11+9, y_from+y_counter*11, 0 )
		display.pixel( x_from+(x_offset+x_counter)*11, y_from+y_counter*11+9, 0 )
		display.pixel( x_from+(x_offset+x_counter)*11+9, y_from+y_counter*11+9, 0 )
		dutil.draw_bitmap( x_from+(x_offset+x_counter)*11+2, y_from+y_counter*11+2, card if disclose_list[idx] else CARD_BACK, CARD_W, CARD_W, 1 )
		x_counter += 1
		if ((idx>17) and (x_counter>4)) or (x_counter>5):
			x_counter = 0
			y_counter += 1
		# Break if used user input while drawing	
		if game.update_input():
			return False # Escaped
	return True


def draw_cursor( cursor_index, cards, disclose_list, x_from, y_from, draw_left ):
	if cursor_index==None:
		return
	x_offset = 0
	x_index  = 0
	y_index  = 0
	if cursor_index>=18:
		x_offset = 0 if draw_left else 1
	# Convert cursor Index to x & y indexes
	y_index = cursor_index//6 
	x_index = cursor_index%6 
	if cursor_index>22: 
		y_index=4+(cursor_index-23)//5
		x_index=(cursor_index-23)%5 
	
	display.fill_rect( x_from+(x_offset+x_index)*11, y_from+y_index*11, 10, 10, 0 )


def play_game():
	# Returen True when everything is rendered... otherwise, return False
	# Drawing may be interrupted in case of user action
	global game 
	# Acquire user move
	game.update_input()
	if game.last_dir.value>0:
		# in game: Enter = select card
		if game.step.value in (STEP_LEFT,STEP_RIGHT):
			# We can read a new one
			if game.last_dir.value==RIGHT:
				game.cursor_index += 1
			elif game.last_dir.value==LEFT:
				game.cursor_index -= 1
			elif game.last_dir.value==DOWN:
				game.cursor_index += (6 if game.cursor_index<17 else 5)
			elif game.last_dir.value==UP:
				game.cursor_index -= (6 if game.cursor_index<17 else 5)
			# constraint le value
			if game.cursor_index>=len(CARDS):
				game.cursor_index -= len(CARDS)
			elif game.cursor_index<0:
				game.cursor_index += len(CARDS)
		
			if (game.last_dir.value==ENTER) and not(game.discloses[game.step.value][game.cursor_index]):
				# not disclosed yet? => we accept the selection
				game.selected[game.step.value] = game.cursor_index
				game.discloses[game.step.value][game.cursor_index] = True # Temporaty disclose it

				# Switch to right panel
				if game.step.value==STEP_LEFT:
					game.init_step( STEP_RIGHT )
				elif game.step.value==STEP_RIGHT:
					game.init_step( STEP_CHECK )

	if game.step.value==STEP_CHECK:
		if (game.last_dir.value>0 and (game.step.elapsed>1000)) or (game.step.elapsed>3000):
			# It is time to append point or to revert the selection
			if game.cards[STEP_LEFT][game.selected[STEP_LEFT]] == game.cards[STEP_RIGHT][game.selected[STEP_RIGHT]]:
				# Add point
				pass
			else:
				game.discloses[STEP_LEFT][ game.selected[STEP_LEFT] ] = False
				game.discloses[STEP_RIGHT][ game.selected[STEP_RIGHT] ]= False

			game.init_step( STEP_LEFT )


	# Display the Left one OR Right one depending on the game ŜTEP
	x_offset = 0
	x_middle = PANEL_WIDTH+CENTER_WIDTH//2
	if game.step.value in (STEP_RIGHT,STEP_CHECK) :
		x_offset = -1*(2*PANEL_WIDTH+CENTER_WIDTH-display.width) # moved to left
		x_middle = display.width-(PANEL_WIDTH+CENTER_WIDTH//2)

	if not draw_cards(game.cards[STEP_LEFT], game.discloses[STEP_LEFT], x_from=0+x_offset , y_from=10, draw_left=True):
		return False # Restart Loop Asap
	if not draw_cards(game.cards[STEP_RIGHT], game.discloses[STEP_RIGHT], x_from=PANEL_WIDTH+CENTER_WIDTH+x_offset, y_from=10, draw_left=False): # 88
		return False
	
	# Blink Cursor over the CURSOR_INDEX card
	#print( game.cursor_blink.elapsed,  game.cursor_blink.value)
	if game.cursor_blink.elapsed>100:
		game.cursor_blink.value = not( game.cursor_blink.value )

	if game.cursor_blink.value:
		if game.step.value==STEP_LEFT:
			draw_cursor( game.cursor_index, game.cards[STEP_LEFT], game.discloses[STEP_LEFT], x_from=0+x_offset , y_from=10, draw_left=True)
		else:
			draw_cursor( game.cursor_index, game.cards[STEP_RIGHT], game.discloses[STEP_RIGHT], x_from=PANEL_WIDTH+CENTER_WIDTH+x_offset, y_from=10, draw_left=False) # 88

	if game.update_input():
		return False

	if game.step.value in (STEP_LEFT,STEP_RIGHT):
		draw_icon( display, HOURGLASSES_ICO[time.time()%3], x_middle-8, 15, 1 )
	elif game.step.value==STEP_CHECK:
		_b = game.cards[STEP_LEFT][game.selected[STEP_LEFT]] == game.cards[STEP_RIGHT][game.selected[STEP_RIGHT]]
		display.fill_rect( x_middle-11, 10, 21, 25, 1 )
		draw_icon( display, SMILE_ICO if _b else THUMB_LOW_ICO, x_middle-8, 15, 0 )


	# Draw draw the selected cards
	if game.selected[STEP_LEFT] != None:
		dutil.scale_bitmap(x_middle-23, display.height-20, game.cards[STEP_LEFT][game.selected[STEP_LEFT]], CARD_W, CARD_W, 1, scale=3 )
	# Draw draw the selected cards
	if game.selected[STEP_RIGHT] != None:
		dutil.scale_bitmap(x_middle+2, display.height-20, game.cards[STEP_RIGHT][game.selected[STEP_RIGHT]], CARD_W, CARD_W, 1, scale=3 )

	_s = "%i/%i" % (len([item for i,item in enumerate(game.discloses[STEP_LEFT]) if item==True and i!=game.selected[STEP_LEFT]]),len(CARDS))
	dtext.text( _s , 0, 0, 1)

	_time = time.time() - game.start_time
	dtext.text( "%i:%02i" %(_time//60,_time%60), 60, 0, 1)

	return True



intro_x = 0
intro_dir = -1
def play_intro():
	global intro_x, intro_dir

	if intro_x < -655:
		intro_dir = +1
	if intro_x > 100:
		intro_dir = -1

	intro_x += intro_dir * 5
	
	display.text( "MEMORY",40, 3 )
	for i in range(len(CARDS)-1):
		x = intro_x + i*28		
		if ( x<-25 ) or ( x-25>display.width ):
			continue
		dutil.scale_bitmap( 5+x, 25, CARDS[i], CARD_W, CARD_W, 1, scale=3 )
	dtext.text( 'Use joystick + enter to play', 0, display.height-8, 1)

#--------------------------
#       GAME LOOP
#--------------------------

while True:
	display.fill(0)
	if game.state.value==INTRO:
		# do not display start screen
		play_intro();
		# start game
		if display.dir!=0: # KeyPressed 
			game.step.value = STEP_SHUFFLE
			game.state.value = PLAYING

	elif game.state.value==PLAYING:

		if game.step.value == STEP_SHUFFLE:
			game.shuffle_cards()
			game.init_step( STEP_LEFT ) # Start Play Left
			game.start_time = time.time()
		else:
			if not play_game():
				continue

	display.show()


