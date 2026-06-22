from machine import Pin, I2C
from mcp230xx import MCP23008
import time

# Reset Red & Green LEDS
i2c = I2C(  1, sda=Pin(6), scl=Pin(7), freq=400000 )
mcp = MCP23008( i2c=i2c, address=0x26 )
mcp.setup( 5, Pin.OUT )
mcp.setup( 6, Pin.OUT ) # RED
mcp.output_pins( {6: False, 5: False} )

btn_b = Pin(2, Pin.IN, Pin.PULL_UP)
btn_a = Pin(3, Pin.IN, Pin.PULL_UP)

# B not pressed? => Execute boot sequence
if btn_b.value():
	# A Pressed? +> start BootMenu
	if btn_a.value()==0:
		f = open( 'autorun.py', 'w')
		f.write( 'module="%s"\n' % 'pyselect' )
		f.close()
		for i in range(10):
			mcp.output_pins( {5:True} )
			time.sleep_ms( 50 )
			mcp.output_pins( {5:False} )
			time.sleep_ms( 50 )


