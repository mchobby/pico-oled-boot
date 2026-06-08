# test_input_screen.py - general input screen usage
#                        With VALIDATION check
#
# See repository: https://github.com/mchobby/pico-oled-boot
#
from oledboot import *
from olededit import EditScreen, STATE_DIGIT

def validate( value ):
    # Validate is called on [OK]
    #
    # Value is a string
    if len(value)==0: 
        return False # can return a boolean value
    if not value.isdigit():
        # Can return message with ValueError exception
        raise ValueError( 'Invalid integer!' )    
    return True


oled = OledBoot()
print( "Showing Input Screen..." )
# Start with Digit Char wheel
scr = EditScreen( oled, 'Integer:', initial_state=STATE_DIGIT, on_validate=validate )
if scr.show():
    oled.fill(0)
    oled.text( scr.value, 1, 0 )
    oled.show()
    print( "Value %i was entered" % int(scr.value) )
else:
    oled.fill(0)
    oled.text( "Cancelled!", 1, 0 )
    oled.show()
print( "That s all folks!" )