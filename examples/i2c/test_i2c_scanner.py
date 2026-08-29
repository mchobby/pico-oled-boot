# test_i2c_scanner.py - Scan the I2C  bus and shows discovered address
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from oledboot import *
from menuboot import *
from fbtext import *
from font8x4 import Font8X4
from icontls import draw_icon # see https://github.com/mchobby/FBGFX/lib/
import time
import micropython

I2C_SPEED = ["400_000", "100_000", "50_000", "10_000" ]

lcd = OledBoot()
menu = MenuBoot(lcd)
text_drawer = FBText( lcd, lcd.width, lcd.height, Font8X4() )

def slice_by( lst, by_len ):
	""" Split a list into sublist of by_len items """
	return [ lst[start:start+by_len] for start in range( 0, len(lst), by_len ) ]

# Initialize screen
lcd.fill(0)
lcd.text('I2C Scanner', (lcd.width-(11*8))//2, 0 )
text_drawer.text('Press START to begin.', 0, 64-30, 1 )
text_drawer.text('Speed change will also', 0, 64-20, 1 )
text_drawer.text('affect the display.',10,64-10, 1 )
lcd.show()
while not( lcd.any_key_pressed ):
	time.sleep_ms(50)


menu.add_label( "0", 'Select speed:', enabled=False )
for s in I2C_SPEED:	
	menu.add_label( s, s )
time.sleep_ms(500)

menu.start()
speed = 0
while speed<=0:
	if menu.update():
		speed = int(menu.selected.code) # the menu code is the speed
	else:
		time.sleep_ms(20)

timeout=50000 #uSec
if speed<50_000:
	timeout=500000

lcd.init_i2c( freq=speed, timeout=timeout )
lcd.fill( 0 )
lcd.text('Scan...', 0, 0)
lcd.show()

counter = 0
while True:
	counter += 1
	try:
		lcd.fill(0)
		lcd.text('Scan %i...' % counter, 0, 0)
		lcd.hline(0, 10, lcd.width, 1)
		lst = [ addr for addr in i2c.scan() if not(addr in (0x26,0x3C))]
		for line_idx, sublist in enumerate( slice_by(lst,2) ):
			s = ", ".join( ["%s (%s)" % (addr,hex(addr)) for addr in sublist] )
			text_drawer.text( s, 0, 12+(line_idx*10), 1 )

		lcd.hline(0, lcd.height-10, lcd.width, 1)
		text_drawer.text( '0x26=MCP, 0x3C=OLED', 0, lcd.height-8, 1 )		
	except Exception as err:
		lcd.fill(0)
		lcd.text( err.__class__.__name__, 0, 10)
		text_drawer.text('%s' % err, 0, 20, 1 )
	lcd.show()
	time.sleep( 2 )
