# Just test the Hardware Layer EXCEPT OLED (used to confirm solder joint
# before adding the OLED display)
# 
# Pressing button A / B do toggle the Red / Green LEDs.
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
import time
from machine import I2C, Pin
from mcp230xx import MCP23008
from micropython import const, alloc_emergency_exception_buf
alloc_emergency_exception_buf(100)

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


class NoOledBoot():
	def __init__( self, mcp_addr=0x26 ):
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

	@property
	def dir( self ):
		""" read and detect directions+Enter+Start """
		vals = self.mcp.input_pins( [0,1,2,3,4,7] )
		return sum( [JOY_VALUES[idx] for idx,value in enumerate(vals) if value==False] )


# ----------------------------------------------------------------------------
#   Test Routines 
# ----------------------------------------------------------------------------

print( "Display joystick direction (+ Enter +Start) on the REPL" )
print( "Pressing button A / B do toggle the Red / Green LEDs." )

labels = {START:"Start", ENTER:"Enter", UP:"Up", DOWN:"Down", LEFT:"Left", RIGHT:"Right"}
lcd = NoOledBoot()

# Using button A & B with IRQ
last_a = time.ticks_ms()
def a_pressed( pin ):
	global lcd, last_a
	# avoids two consecutive changes within 100ms
	if time.ticks_diff( time.ticks_ms(), last_a ) > 100:
		lcd.red.value( not(lcd.red.value()) )
		last_a = time.ticks_ms()

last_b = time.ticks_ms()
def b_pressed( pin ):
	global lcd, last_b
	if time.ticks_diff( time.ticks_ms(), last_b ) > 100:
		lcd.green.value( not(lcd.green.value()) )
		last_b = time.ticks_ms()

lcd.a.irq( handler=a_pressed, trigger=Pin.IRQ_RISING )
lcd.b.irq( handler=b_pressed, trigger=Pin.IRQ_RISING )


while True:
	_d = lcd.dir # Get direction
	if _d in labels:
		print( labels[_d],0,0,1 ) # Text,x,y,color
	elif _d > 0: # 0=No direction
		print( str(_d), 0,0, 1 )
	time.sleep_ms( 100 )
