# test_input_screen.py - general input screen usage
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from oledboot import *
from olededit import EditScreen

oled = OledBoot()
print( "Showing Input Screen..." )
scr = EditScreen( oled, 'Name:', 'David' )
if scr.show():
    oled.fill(0)
    oled.text( scr.value, 1, 0 )
    oled.show()
else:
    oled.fill(0)
    oled.text( "Cancelled!", 1, 0 )
    oled.show()
print( "That s all folks!" )