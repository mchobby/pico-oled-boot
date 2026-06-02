# Pico-I2C-BMP280 - Read Temp & Pressure on BMP280/BME280 via I2C (qwiic port)
#                   And display result on the OLED
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from oledboot import *
from bme280 import BME280
from icontls import draw_icon # see https://github.com/mchobby/FBGFX/lib/
import time
import micropython
micropython.alloc_emergency_exception_buf(100)

# see https://github.com/mchobby/FBGFX/pixel-art/one-bit-pixel-icons/iweather.py
#
# temperature icon
WEATHER52 = [16, 0b0000011111110000, 0b0000110000011000, 0b0000100111001000, 0b0000100111101000, 0b0000100111001000, 0b0000100111101000, 0b0000100101001000, 0b0000100101101000, 0b0000100101001000, 0b0000101101101000, 0b0000101000101000, 0b0000101000101000, 0b0000101101101000, 0b0000100111001000, 0b0000110000011000, 0b0000011111110000 ]
# Cloudy
WEATHER25 = [16, 0b0000000000000000, 0b0000000011111000, 0b0000000010101110, 0b0000000111111010, 0b0000000101001111, 0b0000111110000101, 0b0001100011000111, 0b0001000001101101, 0b0111100000110111, 0b1100110001111110, 0b1000010001001100, 0b1000000000000100, 0b1000000000000100, 0b1100000000001100, 0b0111111111111000, 0b0000000000000000 ]

lcd = OledBoot()
bmp = BME280( i2c=lcd.i2c )
# Initialize screen
lcd.fill(0)
lcd.show()

while True:
	lcd.fill(0) # Clear
	# Draw temperature icon
	draw_icon( lcd, WEATHER52,15,6,1 )
	# Draw Cloudy icon
	draw_icon( lcd, WEATHER25,15,30,1 )
	t,p,h = bmp.values
	lcd.text( t,40,10,1 ) # Text,x,y,color
	lcd.text( p,40,35,1 ) # Text,x,y,color
	lcd.show()
	time.sleep_ms( 300 )
