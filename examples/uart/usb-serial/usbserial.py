# usbserial.py - USB-Serial pass through for Pico-Oled-boot on UART(0) GP0=TX, RX=GP1
#
# Note:
#  * Immediately starts CDC interface
#  * On RP2, starting CDC will terminate the active REPL/MPRemote connexion.
#  * Use a terminal software over the USB CDC connexion
#
# See repository: https://github.com/mchobby/pico-oled-boot
# See MICROPYTHON LIB on USB : https://github.com/micropython/micropython-lib/tree/master/micropython/usb/examples/device
#
from oledboot import *
from menuboot import *
from fbtext import *
from font8x4 import Font8X4
import time, _thread
from micropython import const
from machine import UART
import usb.device
from usb.device.cdc import CDCInterface


print('Starting USB CDC...')
# Zero timeout makes this non-blocking, suitable for os.dupterm().
cdc = CDCInterface(timeout=0)

# pass builtin_driver=True so that we get the built-in USB-CDC alongside,
# if it's available.
usb.device.get().init(cdc, builtin_driver=False)

print("Waiting for USB host to configure the interface...")

# wait for host enumerate as a CDC device...
while not cdc.is_open():
    time.sleep_ms(100)


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


uart_config = UARTConfig()

buf16 = bytearray( 16 ) # UART read buffer
buf16mv = memoryview(buf16)

uart = UART(0,tx=Pin(0),rx=Pin(1),baudrate=9600 )
uart.init( **uart_config.kwargs ) # Set default configuration

last_reset = None # Last time the Reset Stat have been pressed
uart_rx_stat = 0  # shared with Thread
uart_tx_stat = 0
stat_lock = _thread.allocate_lock()
i2c_lock  = _thread.allocate_lock()

def make_main_menu( lcd ):
	menu = MenuBoot(lcd)
	menu.add_label( "UART" , 'UART Config' )
	menu.add_label( "RST"  , 'Reset Stat.' )
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

def stat_disp( lcd ):
	# Perform the Stat Display job
	global buf16, stat_lock, i2c_lock, _disp_thread_halt
	global uart_rx_stat, uart_tx_stat # Global Stats

	_disp_thread_halt = False
	_rx_stat = 0
	_tx_stat = 0
	while not _disp_thread_halt:

		# === Update display ===
		# Display time ~750ms !
		start = time.ticks_ms()
		lcd.fill(0)

		stat_lock.acquire()
		# Mpcam copy of the GLOBAL stat
		_rx_stat = uart_rx_stat
		_tx_stat = uart_tx_stat
		stat_lock.release()

		tdraw.text( uart_config.as_text, 0,0, 1 )
		lcd.hline( 0, 9, 128, 1 )

		lcd.fill_rect( 0,20, 36,32, 1 )
		lcd.text( "UART", 2,32, 0 )
		
		lcd.rect( 128-28, 20, 28, 32, 1 )
		lcd.text( "USB" , 128-26, 32)

		lcd.text( ">", 94, 24, 1 )
		lcd.hline( 38, 27, 60, 1 )
		lcd.text( "<", 35, 42, 1 )
		lcd.hline( 38, 45, 60, 1 )
		s = str(_rx_stat)
		tdraw.text( s, 64-len(s)*5//2, 17, 1 )
		s = str(_tx_stat )
		tdraw.text( s, 64-len(s)*5//2, 35, 1 )

		i2c_lock.acquire()		
		lcd.show()
		_dir = lcd.dir
		i2c_lock.release()
		
		if _dir==START:
			# Reset the GLOBAL statistics
			stat_lock.acquire()			
			uart_rx_stat = 0
			uart_tx_stat = 0
			stat_lock.release()

		# Display time
		# print( time.ticks_diff(time.ticks_ms(),start) )
		time.sleep_ms(100)
	print( "_disp_thread exit")

# Introduction screen
lcd.fill(0)
lcd.text('USB-Serial', (lcd.width-(10*8))//2, 0 )
tdraw.text('press any key', (lcd.width-(14*4))//2, 10, 1 ) 
tdraw.text('START: reset Stat.', 0, 64-30, 1 )
tdraw.text('A: Menu', 0, 64-20, 1 )
tdraw.text('B: ',0,64-10, 1 )
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


	# === Screen Refresh ===
	if state==STATE_DISPLAY:
		# === Capture data ===
		if uart.any():
			cnt = uart.readinto( buf16 )
			if cnt!=None:
				# print( cnt, ':', bytes(buf16mv[0:cnt]) )
				#ring_lock.acquire()
				#ring.put_from( buf16mv[0:cnt] )
				#ring_lock.release()
				cdc.write( buf16mv[0:cnt] )
				stat_lock.acquire()
				uart_rx_stat += cnt
				stat_lock.release()
		cnt = cdc.readinto( buf16 ) # timeout=0 -> no wait!
		if (cnt!=None) and (cnt>0):
			uart.write( buf16mv[0:cnt] )
			stat_lock.acquire()
			uart_tx_stat += cnt
			stat_lock.release()
		# Start display thread if not yet started
		if _disp_thread == None:
			print("Creating _disp_thread")
			_disp_thread = _thread.start_new_thread( stat_disp, (lcd,) )


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

	time.sleep_ms(5)

# speed = int(menu.selected.code) # the menu code is the speed
