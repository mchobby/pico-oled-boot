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
from digit24x24 import Font24X24 as Digit24X24 # Only contains digit definition
import time

lcd = OledBoot()
text_drawer = FBText( lcd, lcd.width, lcd.height, Digit24X24() )

lcd.fill(0) # Clear

# Display reduced charset (for digit font)
lcd.fill(0)
text_drawer.text( "!()+,-./", 0, 0,1 ) # Text,x,y,color
text_drawer.text( ":?[ ]\\" , 0,28,1 ) # Text,x,y,color
lcd.show()
time.sleep( 5 )

lcd.fill(0)
text_drawer.text( "012345", 0, 0,1 ) # Text,x,y,color
text_drawer.text( "6789"  , 0,28,1 ) # Text,x,y,color
lcd.show()
