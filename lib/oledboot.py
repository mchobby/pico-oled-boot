from machine import I2C, Pin
from sh1106 import SH1106_I2C
from mcp230xx import MCP23008
from micropython import const
import time

__version__ = '0.1.3'

DOWN = const(1)
UP   = const(8)
RIGHT= const(4)
LEFT = const(16)
ENTER= const(2)
START= const(32)

JOY_VALUES = [DOWN,ENTER,RIGHT,UP,LEFT,START]

DIR_REPEAT_MS = 150  # Time for automatic direction repeat

class LedAdapter:
	def __init__( self, mcp, gpio ):
		self.mcp = mcp
		self.gpio = gpio
		self.last_value = False

	def value( self, val=None ):
		if val==None:
			return self.last_value
		else:
			self.last_value = val
			return self.mcp.output_pins( {self.gpio: True if val else False} )

	def on( self ):
		self.value( True )

	def off( self ):
		self.value( False )


class ButtonPressed:
	def __init__(self, pin, debounce_ms=10, expire_ms=3000 ):
		# debouce_ms : time required before accepting the pressed state
		# expires_ms : max time to read the pressed state
		self.pin = pin
		self.debounce_ms = debounce_ms
		self.expire_ms = expire_ms
		self.last = None # Last pressed
		self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self.handler )
		
	def handler( self, btn ):
		self.last = time.ticks_ms()

	@property
	def pressed( self ):
		if self.last==None:
			return False
		delta = time.ticks_diff( time.ticks_ms(), self.last )
		if delta<self.debounce_ms:
			return False
		self.last = None
		return delta<self.expire_ms


class OledBoot(SH1106_I2C):
	def __init__( self, oled_addr=0x3c, mcp_addr=0x26, rotate=0 ):
		self.i2c = None
		self.init_i2c( freq=400_000 )
		self.a = Pin( 3, Pin.IN, Pin.PULL_UP )
		self.b = Pin( 2, Pin.IN, Pin.PULL_UP )

		self.__button_a = None # Install ButtonPressed and its hander at the first call
		self.__button_b = None

		self.mcp = MCP23008( i2c=self.i2c, address=mcp_addr )
		self.mcp.setup( 5, Pin.OUT )
		self.mcp.setup( 6, Pin.OUT )
		for _in in (0,1,2,3,4, 7):
			self.mcp.setup( _in, Pin.IN )
			self.mcp.pullup( _in, True )

		self.red = LedAdapter( self.mcp, 6 )
		self.green = LedAdapter( self.mcp, 5 )

		super().__init__( 128, 64, self.i2c, None, oled_addr, rotate=rotate )
		self.sleep(False) # Wake-up the OLED

	def init_i2c( self, **kwarg ):
		if self.i2c:
			del( self.i2c )
		self.i2c = I2C( 1, sda=Pin(6), scl=Pin(7), **kwarg )

	@property
	def any_key_pressed( self ):
		""" Check if any key is pressed """
		# PULLUP logic: LOW means pressed
		if (self.a.value()==0) or (self.b.value()==0):
			return True
		return self.dir in (START,ENTER)

	@property
	def dir( self ):
		""" read and detect directions+Enter+Start """
		vals = self.mcp.input_pins( [0,1,2,3,4,7] )
		return sum( [JOY_VALUES[idx] for idx,value in enumerate(vals) if value==False] )

	@property
	def button_a( self ):
		if self.__button_a==None:
			self.__button_a = ButtonPressed( self.a )
		return self.__button_a

	@property
	def button_b( self ):
		if self.__button_b==None:
			self.__button_b = ButtonPressed( self.b )
		return self.__button_b

