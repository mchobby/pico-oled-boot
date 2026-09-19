# dupterm.py - Duplicate the MicroPython Terminal on the configured UART
#   1) Configure the UART Settings
#   2) Start DupTerm
# Note:
#  * Use a terminal software over the UART to get copy of the REPL
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from oledboot import *
from menuboot import *
from fbtext import *
from font8x4 import Font8X4
import time, sys
from micropython import const
from machine import UART
from os import dupterm



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

uart = UART(0,tx=Pin(0),rx=Pin(1),baudrate=9600 )
uart.init( **uart_config.kwargs ) # Set default configuration


def make_main_menu( lcd ):
	menu = MenuBoot(lcd)
	menu.add_label( "UART" , 'UART Config' )
	menu.add_label( "START", 'DupTerm start' )
	return menu


def make_uart_menu( lcd ):
	menu = MenuBoot(lcd)
	menu.add_combo( "BAUD"  , 'Bauds: %s', [(str(baud),str(baud)) for baud in BAUD_RATES], uart_config.baudrate ) 
	menu.add_combo( "BITS"  , 'Data : %s bits' , [("9","9"), ("8","8"), ("7","7")], uart_config.bits)
	menu.add_combo( "PARITY", 'Parit: %s' , [("N","None"), ("E","Even"), ("O","Odd")], uart_config.parity)
	menu.add_combo( "STOPBIT",'Stop : %s bits' , [("0","0"), ("1","1"), ("2","2")], uart_config.stop)
	menu.add_label( "APPLY"  , 'Apply' )
	return menu



# Introduction screen
lcd.fill(0)
lcd.text('DupTerm', (lcd.width-(7*8))//2, 0 )
tdraw.text('press any key', (lcd.width-(14*4))//2, 10, 1 ) 
tdraw.text('Replicate Micropython', 0, 64-20, 1 )
tdraw.text('REPL over UART.', 0, 64-10, 1 )
#tdraw.text('B: ',0,64-10, 1 )
lcd.show()
while not( lcd.any_key_pressed ):
	time.sleep_ms(10)

time.sleep_ms(500)

# Current Display State
STATE_MAIN_MENU = const(1)
STATE_UART_MENU = const(2)

state = STATE_MAIN_MENU # Current display state
menu = make_main_menu( lcd )
menu.start()

while True:
	# === Screen Refresh ===
	if state==STATE_MAIN_MENU:
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
			elif entry.code=="START":
				# Start the DupTerm
				lcd.fill(0)
				tdraw.text( uart_config.as_text, 0,0, 1 )
				lcd.hline( 0, 9, 128, 1 )
				tdraw.text( 'DupTerm started on UART(0)', 0, 17, 1 )
				tdraw.text( 'Connect your terminal on' , 0, 27, 1 )
				tdraw.text( '   GP(0)=tx & GP(1)=rx', 0, 37, 1 )
				tdraw.text( 'Script exit!', 0, 47, 1 )
				lcd.show()
				break


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
				state=STATE_MAIN_MENU
				if menu:
					del(menu)
				menu = make_main_menu( lcd )
				menu.start()

	time.sleep_ms(5)

# speed = int(menu.selected.code) # the menu code is the speed
dupterm(uart)
print('Free-up ressources...')
if menu!=None:
	del(menu)
del( uart_config )
del( state )
del( tdraw )
del( lcd )
import gc
gc.collect()
print( '%i bytes free' % gc.mem_free() )
