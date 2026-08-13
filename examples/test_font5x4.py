# test_font8x4.py : Display custom font on the Pico-Oled-Boot
#
# The FBGFX library installed with the Pico-Oled-Boot does
# offers a Custom Font drawing with fbtext.py .
# fbtext.py work with any FrameBuffer based implementation.
#
# Find more Font in lib & lib-optional folder of FBGFX
#   https://github.com/mchobby/esp8266-upy/tree/master/FBGFX
#
from oledboot import *
from fbtext import *
from font5x4 import Font5X4
import time

lcd = OledBoot()
text_drawer = FBText( lcd, lcd.width, lcd.height, Font5X4() )

lcd.fill(0) # Clear

label = 'AAA'
text_drawer.text( label, 10,30,1 ) # Text,x,y,color
print( "Label %s has %i pixels wide" % (label, text_drawer.font.text_width(label) ) )
lcd.show()
time.sleep( 2 )

# Display charset
lcd.fill(0)
text_drawer.text( "abcdefghijklmnopqrstuvw", 0,0 ,1 ) # Text,x,y,color
text_drawer.text( "xyz @_^0123456789!?\"#$%", 0,10,1 ) # Text,x,y,color
text_drawer.text( "&'()[]=*+,-./\\:;<>", 0,20,1 ) # Text,x,y,color
text_drawer.text( "----------------------------", 0,30,1 ) # Text,x,y,color
lcd.show()
