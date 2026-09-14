# serialmon.py - Serial Monitor for Pico-Oled-boot on UART(0) GP0=TX, RX=GP1
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from oledboot import *
from menuboot import *
from fbtext import *
from font8x4 import Font8X4
from icontls import draw_icon # see https://github.com/mchobby/FBGFX/lib/
import time, _thread
from micropython import const
from machine import UART
from ringbuf import RingBuffer
from maps import slice_by

RING_BUF_SIZE = 512 

DEFAULT_MODE  = "HEX" # Display Mode
DEFAULT_SEP   = "CR" # Send Separator
DEFAULT_LOG   = "OFF" # FILE=Log to file, OFF=Log off

BAUD_RATES = (115200,57600,38400,9600,4800,1200,300)
DEFAULT_BAUD = "9600"
DEFAULT_BITS = "8"
DEFAULT_PARITY = "N"
DEFAULT_STOPBIT = "1"

lcd = OledBoot()
lcd.button_a.debounce_ms = 150 # Increase debouing
lcd.button_b.debounce_ms = 150
tdraw = FBText( lcd, lcd.width, lcd.height, Font8X4() )

class UARTConfig:
	def __init__( self ):
		# Use KWarg to pass parameter to UART
		self.kwargs = {'bits':int(DEFAULT_BITS), 'parity': self.parity_int(DEFAULT_PARITY), 'stop':int(DEFAULT_STOPBIT), 'baudrate':int(DEFAULT_BAUD) }

	def parity_int( self, str_value ):
		if str_value=="N":
			return None
		elif str_value=="E":
			return 0
		elif str_value=="O":
			return 1
		else:
			raise ValueError( "Invalid %s str value" % str_value )

	def parity_str( self, int_value ):
		if int_value==None:
			return "N"
		elif int_value==0:
			return "E" # Even
		elif int_value==1:
			return "O" # Odd
		else:
			raise ValueError( "Invalid %s int value" % int_value )


	@property
	def baudrate( self ): # Baudrate as handled by the menu (a string)
		return str(self.kwargs['baudrate'])

	@baudrate.setter
	def baudrate( self, value ):
		self.kwargs['baudrate'] = int(value)

	@property
	def bits( self ):
		return str(self.kwargs['bits'])

	@bits.setter
	def bits( self, value ):
		self.kwargs['bits'] = int(value)

	@property
	def stop( self ):
		return str(self.kwargs['stop'])

	@stop.setter
	def stop( self, value ):
		self.kwargs['stop'] = int(value)

	@property 
	def parity( self ):
		return self.parity_str( self.kwargs['parity'] )

	@parity.setter
	def parity( self, str_value ):
		self.kwargs['parity'] = self.parity_int( str_value )

	@property
	def as_text( self ):
		return "%s%s%s @ %s" % ( self.bits, self.parity, self.stop, self.baudrate)

class APPConfig:
	def __init__( self ):
		self.mode = DEFAULT_MODE
		self.sep  = DEFAULT_SEP
		self.log  = DEFAULT_LOG

uart_config = UARTConfig()
app_config = APPConfig()

buf16 = bytearray( 16 ) # UART read buffer
buf16mv = memoryview(buf16)
ring = RingBuffer( RING_BUF_SIZE, run_over=True ) # overwrite buffer content
ring_lock = _thread.allocate_lock()
i2c_lock = _thread.allocate_lock()
uart = UART(0,tx=Pin(0),rx=Pin(1),baudrate=9600 )
uart.init( **uart_config.kwargs ) # Set default configuration
paused= False # Pause data acquisition
last_paused= time.ticks_ms()

def make_main_menu( lcd ):
	menu = MenuBoot(lcd)
	menu.add_label( "UART" , 'UART Config' )
	menu.add_combo( "MODE" , 'Mode: %s' , [("HEX","Hex."),("ASCII","Ascii"),("PLOT","Plotter")], app_config.mode  )
	menu.add_combo( "SEP"  , 'Sep : %s' , [("CR","CR"), ("CRLF","CR/LF"), ("LF","LF"), ("NONE", 'None')], app_config.sep )
	menu.add_combo( "LOG"  , 'Log : %s' , [("FILE","File"),("OFF","off")], app_config.log )
	return menu


def make_uart_menu( lcd ):
	menu = MenuBoot(lcd)
	menu.add_combo( "BAUD"  , 'Bauds: %s', [(str(baud),str(baud)) for baud in BAUD_RATES], uart_config.baudrate ) 
	menu.add_combo( "BITS"  , 'Data : %s bits' , [("9","9"), ("8","8"), ("7","7")], uart_config.bits)
	menu.add_combo( "PARITY", 'Parit: %s' , [("N","None"), ("E","Even"), ("O","Odd")], uart_config.parity)
	menu.add_combo( "STOPBIT",'Stop : %s bits' , [("0","0"), ("1","1"), ("2","2")], uart_config.stop)
	menu.add_label( "APPLY"  , 'Apply' )
	return menu

_disp_thread_halt = False # Halting the display thread
_disp_thread = None

def serialmon_disp( lcd ):
	# Perform the SerialMonitor job
	global buf16, paused, ring_lock, i2c_lock, _disp_thread_halt
	_disp_thread_halt = False

	_top_pos = None # Position of the top-left char to display
	while not _disp_thread_halt:

		# === Update display ===
		# Display time ~750ms !
		start = time.ticks_ms()
		lcd.fill(0)
		# 8 bytes per line * 5 lines
		read_max = 40

		if not(paused) or (_top_pos==None): # auto-follow or initialize
			ring_lock.acquire()
			if ring.available_for_reading<read_max:
				read_max = ring.available_for_reading
			# Copy the last max_len bytes from ring_buffer
			_top_pos = ring.index_put-read_max			
			data = ring.copy_from( _top_pos, read_max )
			ring_lock.release()
		else: # we are paused
			ring_lock.acquire()
			data = ring.copy_from( _top_pos, read_max )
			ring_lock.release()

		dlines =  slice_by( data, 8 )
		for lidx, dline in enumerate(dlines):
			for cidx in range( 0, len(dline), 2 ): # By step of two			
				tdraw.text( hex(dline[cidx])[2:]  , cidx//2*21   +(cidx//4), 11+lidx*10, 1 )
				tdraw.text( hex(dline[cidx+1])[2:], cidx//2*21+10+(cidx//4), 11+lidx*10, 1 )
			for cidx, c in enumerate(dline):
				tdraw.text( chr(c), 87+cidx*5, 11+lidx*10, 1 )

		#print( "put", ring.index_put, "get", ring.index_get, "Free", ring.free, "Avail for reading", ring.available_for_reading )

		# Status Bar
		if paused:
			tdraw.text( "Cursor: %i / %i" % (_top_pos, ring.size), 0,0,1 )
		else:
			tdraw.text( uart_config.as_text, 0,0, 1 )
		
		tdraw.text( "paused" if paused else "run", 96,0, 1)
		lcd.hline( 0, 9, 128, 1 )
		lcd.vline( 85,11,53, 1)
		# content
		i2c_lock.acquire()
		lcd.show()
		_dir = lcd.dir
		i2c_lock.release()
		
		if paused: # Calculate new cursor position
			print(_dir)
			if _dir==UP:
				_top_pos -= 8 # One line up
				_top_pos = _top_pos % ring.size
				#if _top_pos<=ring.index_get:
				#	_top_pos = ring.index_get
			if _dir==DOWN:
				_top_pos += 8
				_top_pos = _top_pos % ring.size
				#if top_pos >= ring.index_put-1-40: # 40 is nbr of char that can be read
				#	_top_pos = ring.index_put-1-40
		# Display time
		# print( time.ticks_diff(time.ticks_ms(),start) )
	print( "_disp_thread exit")

# Introduction screen
lcd.fill(0)
lcd.text('Serial Monitor', (lcd.width-(14*8))//2, 0 )
tdraw.text('START: begin/stop.', 0, 64-30, 1 )
tdraw.text('A: Menu show/hide', 0, 64-20, 1 )
tdraw.text('B: Send',0,64-10, 1 )
i2c_lock.acquire()
lcd.show()
while not( lcd.any_key_pressed ):
	time.sleep_ms(10)
i2c_lock.release()

time.sleep_ms(500)


# Current Display State
STATE_DISPLAY   = const(0)
STATE_MAIN_MENU = const(1)
STATE_UART_MENU = const(2)

state = STATE_DISPLAY # Current display state
menu  = None
while True:
	# === User Input ===
	i2c_lock.acquire()
	_dir = lcd.dir
	i2c_lock.release()
	if lcd.button_a.pressed:
		if state in (STATE_MAIN_MENU,STATE_UART_MENU):
			state=STATE_DISPLAY		
		else:
			state=STATE_MAIN_MENU
			if _disp_thread != None: # Exit display Thread if running
				_disp_thread_halt = True # Halting the display thread
				_disp_thread = None
				time.sleep_ms(500)
			print( "Start main menu")
			if menu:
				del( menu )
			menu = make_main_menu( lcd )
			menu.start()
	elif lcd.button_b.pressed:
		print("B WAS PRESSED BUT NOT IMPLEMENTED")
		if _disp_thread != None: # Exit display Thread if running
			_disp_thread_halt = True # Halting the display thread
			_disp_thread = None
			time.sleep_ms(500)

	elif _dir==START:
		if time.ticks_diff(time.ticks_ms(),last_paused)>500:
			paused = not(paused)
			print( "update paused", paused)
			last_paused = time.ticks_ms()
		


	# === Screen Refresh ===
	if state==STATE_DISPLAY:
		# === Capture data ===
		if not(paused) and uart.any():
			cnt = uart.readinto( buf16 )
			if cnt!=None:
				# print( cnt, ':', bytes(buf16mv[0:cnt]) )
				ring_lock.acquire()
				ring.put_from( buf16mv[0:cnt] )
				ring_lock.release()
					# Start display thread if not yet started
		if _disp_thread == None:
			print("Creating _disp_thread")
			_disp_thread = _thread.start_new_thread( serialmon_disp, (lcd,) )


	elif state==STATE_MAIN_MENU:
		if menu.update():
			entry = menu.selected # will reset selection (IMPORTANT!)
			if not(entry):
				continue
			if entry.code=="UART":
				state = STATE_UART_MENU
				if menu:
					del(menu)
				menu = make_uart_menu( lcd )
				menu.start()
			elif entry.code=="LOG":
				app_config.log = entry.cargo.value
				print( "log", app_config.log )
			elif entry.code=="MODE":
				app_config.mode = entry.cargo.value
				print( "mode", app_config.mode )
			elif entry.code=="SEP":
				app_config.sep = entry.cargo.value
				print( "sep", app_config.sep )

	elif state==STATE_UART_MENU:		
		if menu.update():
			entry = menu.selected
			if entry and (entry.code=="APPLY"):
				print("Apply UART setting")
				uart_config.baudrate = menu.by_code('BAUD').cargo.value
				uart_config.bits     = menu.by_code('BITS').cargo.value
				uart_config.stop     = menu.by_code('STOPBIT').cargo.value
				uart_config.parity   = menu.by_code('PARITY').cargo.value
				uart.init( **uart_config.kwargs )
				state=STATE_DISPLAY

	time.sleep_ms(20)

# speed = int(menu.selected.code) # the menu code is the speed
