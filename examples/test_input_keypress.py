# test_input_screen.py - general input screen usage
#                        With KEY PRESS check
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from oledboot import *
from olededit import EditScreen

def key_filter( owner, key ):
    # Owner is the EditScreen instance to give accès to the current value
    return key!=32 # Do not allow Space char

oled = OledBoot()
print( "Showing Input Screen..." )
scr = EditScreen( oled, 'No Space Value:', on_key_press=key_filter )
if scr.show():
    oled.fill(0)
    oled.text( scr.value, 1, 0 )
    oled.show()
else:
    oled.fill(0)
    oled.text( "Cancelled!", 1, 0 )
    oled.show()
print( "That s all folks!" )