# Clock-Digital.py : Display a digital clock
#
from oledboot import *
from fbtext import *
from braille24x24 import Font24X24 as Braille24X24
from font8x4 import Font8X4
from machine import RTC, I2C, Pin
import time, sys

mcu_rtc = RTC()
lcd = OledBoot()

# Try to detect External RTC
error_msg = None
addrs = lcd.i2c.scan()

# PCF8523 doesnt always enumerate on i2c.scan()
# So try to mount it the brutal way
try:
	from pcf8523 import PCF8523
	ext_rtc = PCF8523(lcd.i2c)
	print( 'PCF8523 datetime :', ext_rtc.datetime )
	mcu_rtc.datetime( ext_rtc.datetime )
except Exception as err:
	error_msg = ['PCF8523 RTC init failed!', '%s' % err ]


WAIT_TIME = 5
if not error_msg is None:
	lcd.fill(0)
	lcd.text(error_msg[0][ 0:16], 0, 0, 1 )
	lcd.text(error_msg[0][16:32], 0, 10, 1 )
	lcd.hline( 0,22, lcd.width, 1 )
	lcd.text(error_msg[1][ 0:16], 0, 25, 1 )
	lcd.text(error_msg[1][16:32], 0, 35, 1 )	
	lcd.text(error_msg[1][32:48], 0, 45, 1 )
	for i in range( WAIT_TIME, 0, -1 ):
		print( "Waiting...", i )
		lcd.fill_rect( 0,  lcd.height-8, lcd.width, 8, 0 )
		lcd.text('Wait %i sec' % i, 0, lcd.height-8, 1 )
		lcd.show()	
		time.sleep( 1 )
	



braille_drawer = FBText( lcd, lcd.width, lcd.height, Braille24X24() )
text_drawer = FBText( lcd, lcd.width, lcd.height, Font8X4() )

while True:
	lcd.fill(0) # Clear

	# Get Date Time
	y,m,d,wd,hh,mm,ss,ms = mcu_rtc.datetime()

	# --- Draw time ---
	braille_drawer.text( "%02i" % hh, 2, 2, 1 ) # Text,x,y,color
	text_drawer.text('H',49,18,1)

	braille_drawer.text( "%02i" % mm, 70, 2, 1 ) # Text,x,y,color
	text_drawer.text('M',117,18,1)

	braille_drawer.text( "%02i" % ss, 35, 35, 1 ) # Text,x,y,color
	text_drawer.text('S',82,52,1)
	
	
	lcd.show()
	time.sleep_ms( 50 )

