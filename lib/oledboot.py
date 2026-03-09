from machine import I2C, Pin
from sh1106 import SH1106_I2C
from mcp230xx import MCP23008
from micropython import const

DOWN = const(1)
UP   = const(8)
RIGHT= const(4)
LEFT = const(16)
ENTER= const(2)
START= const(32)

JOY_VALUES = [DOWN,ENTER,RIGHT,UP,LEFT,START]

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


class OledBoot(SH1106_I2C):
	def __init__( self, oled_addr=0x3c, mcp_addr=0x26 ):
		self.i2c = I2C( 1, sda=Pin(6), scl=Pin(7), freq=400000 )
		self.a = Pin( 3, Pin.IN, Pin.PULL_UP )
		self.b = Pin( 2, Pin.IN, Pin.PULL_UP )


		self.mcp = MCP23008( i2c=self.i2c, address=mcp_addr )
		self.mcp.setup( 5, Pin.OUT )
		self.mcp.setup( 6, Pin.OUT )
		for _in in (0,1,2,3,4, 7):
			self.mcp.setup( _in, Pin.IN )
			self.mcp.pullup( _in, True )

		self.red = LedAdapter( self.mcp, 6 )
		self.green = LedAdapter( self.mcp, 5 )

                super().__init__( 128, 64, self.i2c, None, oled_addr )
                self.sleep(False) # Wake-up the OLED


	@property
	def dir( self ):
		""" read and detect directions+Enter+Start """
		vals = self.mcp.input_pins( [0,1,2,3,4,7] )
		return sum( [JOY_VALUES[idx] for idx,value in enumerate(vals) if value==False] )


