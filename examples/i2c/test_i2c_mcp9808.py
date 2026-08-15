# test_i2c_mcp9808.py - Show Temperature (high precision) on pico-oled-boot 
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from oledboot import *
from mcp9808 import MCP9808
from icontls import draw_icon # see https://github.com/mchobby/FBGFX/lib/
import time
import micropython
micropython.alloc_emergency_exception_buf(100)

# see https://github.com/mchobby/FBGFX/pixel-art/one-bit-pixel-icons/iweather.py
#
# temperature icon
WEATHER52 = [16, 0b0000011111110000, 0b0000110000011000, 0b0000100111001000, 0b0000100111101000,
             0b0000100111001000, 0b0000100111101000, 0b0000100101001000, 0b0000100101101000, 0b0000100101001000,
             0b0000101101101000, 0b0000101000101000, 0b0000101000101000, 0b0000101101101000, 0b0000100111001000,
             0b0000110000011000, 0b0000011111110000 ]

lcd = OledBoot()
mcp = MCP9808( i2c=lcd.i2c, address=0x1F )
# Initialize screen
lcd.fill(0)
lcd.show()

while True:
	lcd.fill(0) # Clear
	# Draw temperature icon
	draw_icon( lcd, WEATHER52,15,6,1 )
	t = mcp.temperature
	lcd.text( "%2.2f C" % t,40,10,1 ) # Text,x,y,color
	lcd.show()
	time.sleep_ms( 300 )
