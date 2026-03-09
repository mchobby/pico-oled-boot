# Pico-Oled-Boot - Display joystick direction (+ Enter +Start) on the display
#                  Pressing button A / B do toggle the Red / Green LEDs.
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from oledboot import *
import time
import micropython
micropython.alloc_emergency_exception_buf(100)

labels = {START:"Start", ENTER:"Enter", UP:"Up", DOWN:"Down", LEFT:"Left", RIGHT:"Right"}
lcd = OledBoot()
# Initialize screen
lcd.fill(0)
lcd.show()


# Using button A & B with IEQ
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
	lcd.fill(0) # Clear
	_d = lcd.dir # Get direction
	if _d in labels:
		lcd.text( labels[_d],0,0,1 ) # Text,x,y,color
	elif _d > 0: # 0=No direction
		lcd.text( str(_d), 0,0, 1 )
	lcd.show()
	time.sleep_ms( 100 )
