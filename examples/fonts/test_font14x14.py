# test_font14x14.py : Display custom font on the Pico-Oled-Boot
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
from font14x14 import Font14X14
import time

lcd = OledBoot()
text_drawer = FBText( lcd, lcd.width, lcd.height, Font14X14() )

lcd.fill(0) # Clear

label = 'AB C'
text_drawer.text( label, 10,30,1 ) # Text,x,y,color
print( "Label %s has %i pixels wide" % (label, text_drawer.font.text_width(label) ) )
lcd.show()
time.sleep( 2 )

# Display charset
lcd.fill(0)
text_drawer.text( "abcdefghij", 0,0 ,1 ) # Text,x,y,color
text_drawer.text( "klmnopqrst", 0,16,1 ) # Text,x,y,color
text_drawer.text( "uvwxyz @_^", 0,32,1 ) # Text,x,y,color
text_drawer.text( "0123456789", 0,48,1 ) # Text,x,y,color
lcd.show()
time.sleep( 2 )

lcd.fill(0)
text_drawer.text( "!?\"#$%&'", 0,0 ,1 ) # Text,x,y,color
text_drawer.text( "()[]=*+,-.", 0,16,1 ) # Text,x,y,color
text_drawer.text( "/\\:;<>", 0,32,1 ) # Text,x,y,color
lcd.show()
