""" MicroPython Input Editor for PICO-OLED-BOOT - use I2C OLED + I2C MCP23008

See project https://github.com/mchobby/pico-oled-boot

domeu, 4 june 2026, Initial Writing (shop.mchobby.be)
----------------------------------------------------------------------------

MCHobby invest time and ressource in developping project and libraries.
It is a long and tedious work developed with Open-Source mind and freely available.
IF you like our work THEN help us by buying your product at MCHobby (shop.mchobby.be).

----------------------------------------------------------------------------
Copyright (C) 2026  - Meurisse D. (shop.mchobby.be)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

__version__ = '0.0.1'

# from icons8 import NO
# from icontls import draw_icon
from oledboot import UP,DOWN,RIGHT,LEFT,ENTER,DIR_REPEAT_MS
from micropython import const
from icontls import draw_icon
import time

# === Special Keys ===
KEY_BS        = 8 
KEY_CR        = 13  # OK button
KEY_ESC       = 27  # CANCEL button
KEY_SHIFT_IN  = 15  # Shift IN
KEY_SHIFT_OUT = 14  # Shift OUT or Symbol/Substitute OUT or Digit/Unit out
KEY_SYMBOL    = 26  # Symbol/Substitute IN (eg: symbol)
KEY_DIGIT     = 31  # Digit/Unit IN
# KEY_CLEAR     = const( 127 ) # Clear/Delete field

# Representation of special keys
KEY_LABELS = { KEY_BS: "<<<", KEY_CR:"[V]", KEY_ESC:"[X]", KEY_SHIFT_IN:"{U}", KEY_SHIFT_OUT:"{_}", KEY_SYMBOL:"{@}", KEY_DIGIT:"{#}" }
KEY_OK = KEY_CR
KEY_CANCEL = KEY_ESC
# Doc string hlper for the special keys
KEY_HELPERS = { KEY_BS: "Delete", KEY_CR:"Confirm", KEY_ESC:"Cancel", KEY_SHIFT_IN:"Upper", KEY_SHIFT_OUT:"Normal", KEY_SYMBOL:"Symbols", KEY_DIGIT:"Digits" }

# === Key Whell STATE  ===
# What kind of characters Set we are displaying
STATE_NORMAL = const(0) # Display normal char
STATE_SHIFTED= const(1) # Display Uppercase Char
STATE_DIGIT  = const(2) # Display Digit + Decimal_Separator
STATE_SYMBOL = const(3) # Displat @, #, (, ...
# Collections of Characters Set
CHAR_COLS = { STATE_NORMAL : list([i for i in range(97,123)]+[32,KEY_BS,KEY_SHIFT_IN,KEY_DIGIT,KEY_SYMBOL]),
              STATE_SHIFTED: list([i for i in range(65,91)]+[32,KEY_BS,KEY_DIGIT,KEY_SYMBOL,KEY_SHIFT_OUT]),
              STATE_DIGIT  : list([i for i in range(48,58)]+[46,KEY_BS,KEY_SHIFT_OUT]),
              STATE_SYMBOL : list([i for i in range(33,48)]+[i for i in range(58,65)]+[i for i in range(91,65)]+[123,124,125,126,KEY_BS,KEY_SHIFT_OUT]),
    }
# === Current Focus ===
FOCUS_WHEEL  = const(0)
FOCUS_OK     = const(1)
FOCUS_CANCEL = const(2)


YES = [5, 0b00000, 0b00001, 0b00010, 0b10100, 0b01000]
NO  = [5, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001]
UP_ARROW   = [5, 0b00100, 0b01110, 0b01110, 0b11111, 0b11111]
DOWN_ARROW = [5, 0b11111, 0b11111, 0b01110, 0b01110, 0b00100]
LEFT_ARROW = [5, 0b00011, 0b01111, 0b11111, 0b01111, 0b00011]
RIGHT_ARROW= [5, 0b11000, 0b11110, 0b11111, 0b11110, 0b11000]

class EditScreen:
        def __init__( self, oled_boot, label, initial_value='', on_key_press=None, on_validate=None, initial_state=STATE_NORMAL ):
                self.oled = oled_boot
                self.label= label
                self.value= initial_value
                self.on_key_press=on_key_press # key_press(owner, key):bool to accept the last added char.
                self.on_validate=on_validate   # validate(value):True/False or ValueError Exception
                
                # Internals
                self.state = None
                self._col  = None
                self._col_index = None
                
                self.focus = FOCUS_WHEEL
                self.set_state( initial_state )
                
        def is_printable( self, key ):
            return ( 32<=key<=126 )
        
        def key_as_text( self, key ):
            if self.is_printable( key ):
                return chr( key )
            else:
                return KEY_LABELS[key]
            
        def get_helper( self, key ):
            if key in KEY_HELPERS:
                return KEY_HELPERS[key]
            return None

        def set_state( self, new_state ):
            if new_state != self.state:
                self.state = new_state # Character Set
                self._col  = CHAR_COLS[self.state] # Key collections to be used
                self._col_index = 0 # Current selection in the collection
                self.focus = FOCUS_WHEEL
                

        def fire_key_press( self, key ):
            # key: the pressed key (a char) or a special charaters char
            if self.on_key_press!=None:
                return self.on_key_press( self, key )
            return True
                      
        def fire_validate( self ):
            if self.on_validate == None:
                return True
            
            try:
                _r = self.on_validate(self.value)
                if _r==False:
                    self.draw_msg( 'Invalid!', 1000 )
                return _r
            except ValueError as err:
                self.draw_msg( '%s' % err, 1000 )
                return False
     
        def draw_letter_wheel( self ):
            # Selected Key/Letter
            _key = self._col[self._col_index]
            _y = self.oled.height//2
            if _key==32: # Space is treated differently
                _format = " %s "
            elif self.is_printable(_key):
                _format = " %s "
            else:
                _format = "%s"
            _text = _format % self.key_as_text(_key)
            _width = len(_text)*8
            _x = (self.oled.width-_width)//2
            
            # Draw character selector
            self.oled.fill_rect( _x-1, _y-4, 26, 14, 1 if self.focus==FOCUS_WHEEL else 0 )
            self.oled.text( _text, _x, _y, 0 if self.focus==FOCUS_WHEEL else 1)
            # Remaining Left/Right Space
            _max_width = (self.oled.width//2)-(_width//2)
            # Right text to display
            _right_text = ''
            _index = self._col_index
            while (len(_right_text)*8) < _max_width:
                _index+=1
                _index = 0 if _index>=len(self._col) else _index
                _s = self.key_as_text( self._col[_index] )
                if (len(_right_text)+len(_s))*8 <= _max_width:
                    _right_text += _s
                else:
                    break
            self.oled.text( _right_text, self.oled.width-_max_width, _y )
            # Left text to display
            _left_text = ""
            _index = self._col_index
            while (len(_left_text)*8) < _max_width:
                _index-=1
                _index = len(self._col)-1 if _index<0 else _index
                _s = self.key_as_text( self._col[_index] )
                if (len(_left_text)+len(_s))*8 <= _max_width:
                    _left_text = _s + _left_text
                else:
                    break
            self.oled.text( _left_text, _max_width-len(_left_text)*8, _y )
            
            # Draw helper
            _helper = self.get_helper( _key )
            if _helper:
                self.oled.text( _helper, 0 , self.oled.height-10 ) # self.oled.width-len(_helper)*8
            else:
                # Draw the arrows
                draw_icon( self.oled, LEFT_ARROW ,  2, self.oled.height-10, 1 )
                draw_icon( self.oled, UP_ARROW   , 12, self.oled.height-10, 1 )
                draw_icon( self.oled, DOWN_ARROW , 22, self.oled.height-10, 1 )
                draw_icon( self.oled, RIGHT_ARROW, 32, self.oled.height-10, 1 )
            
        def draw_label( self ):
            self.oled.text( self.label, 0, 0 )
            
        def draw_msg( self, msg, delay_ms ):
            # Overlaps the "Letter Wheel" with a message for délay_ms
            _width = len(msg)*8
            _x = (self.oled.width-_width)//2
            _y = self.oled.height//2

            self.oled.fill_rect( 0, _y-4, self.oled.width, 14, 0 )
            self.oled.text( msg, _x, _y, 1 )
            self.oled.show()
            time.sleep_ms( delay_ms )            
            
        def draw_value( self ):
            # Draw the current value + Bliking Cursor
            _y = 12
            _x = 2
            _max_width = self.oled.width-_x-3
            _value = self.value + (" " if time.time()%2==0 else "_")
            while len(_value)*8 > _max_width:
                _value = _value[1:] 
            self.oled.text( _value, _x+1, _y+1 )
            self.oled.rect( _x-2, _y-2, _max_width+2, 8+5, 1 )
            
        def draw_button( self ):
            _x = self.oled.width-65
            _y = self.oled.height-12
            fg = 0 if self.focus==FOCUS_OK else 1
            bg = 0 if fg==1 else 1
            self.oled.fill_rect( _x-2, _y, 26, 11, bg )
            draw_icon( self.oled, YES, _x, _y+3, fg )
            self.oled.text( 'OK', _x+7, _y+2, fg )
            self.oled.rect( _x-3, _y-1, 28, 13, 1 )
            self.oled.pixel( _x-3, _y-1, 0 ) # Corners
            self.oled.pixel( _x+24, _y-1, 0 )
            self.oled.pixel( _x-3, _y+11, 0 ) 
            self.oled.pixel( _x+24, _y+11, 0 )
            
            fg = 0 if self.focus==FOCUS_CANCEL else 1
            bg = 0 if fg==1 else 1
            self.oled.fill_rect( _x+27, _y, 34, 11, bg )
            draw_icon( self.oled, NO, _x+30, _y+3, fg )
            self.oled.text( 'Cnl', _x+37, _y+2, fg )
            self.oled.rect( _x+27, _y-1, 35, 13, 1 )
            self.oled.pixel( _x+27, _y-1, 0 ) # Corners
            self.oled.pixel( _x+61, _y-1, 0 )
            self.oled.pixel( _x+27, _y+11, 0 )
            self.oled.pixel( _x+61, _y+11, 0 )
            
        def _refresh( self ):
            # refesh the screen content
            self.oled.fill(0)
            self.draw_letter_wheel()
            self.draw_label()
            self.draw_value()
            self.draw_button()
            self.oled.show()
        
        def show( self ):
            self._col_index = 5 # Start further in the list tp avoids extra option displays
            _last = time.ticks_ms()-DIR_REPEAT_MS
            _last_dir = None
            while True:
                # Auto repeat read
                _dir = self.oled.dir
                if _dir!=_last_dir: # Change is immediately accepted
                    _last = time.ticks_ms()
                    _last_dir = _dir
                elif (_dir>0) and (time.ticks_diff( time.ticks_ms(), _last )>DIR_REPEAT_MS):                    
                    _last = time.ticks_ms()
                else:
                    _dir = None
                
                # Acting depending on direction
                if _dir==RIGHT:
                    if self.focus==FOCUS_WHEEL:
                        self._col_index +=1
                        if self._col_index >= len(self._col):
                            self._col_index = 0
                    else:
                        self.focus = FOCUS_CANCEL if self.focus==FOCUS_OK else FOCUS_OK
                        
                elif _dir==LEFT:
                    if self.focus==FOCUS_WHEEL:
                        self._col_index -=1
                        if self._col_index < 0:
                            self._col_index = len(self._col)-1
                    else:
                        self.focus = FOCUS_CANCEL if self.focus==FOCUS_OK else FOCUS_OK
                        
                elif _dir==DOWN:
                    self.focus += 1
                    if self.focus>FOCUS_CANCEL:
                        self.focus=FOCUS_WHEEL
                        
                elif _dir==UP:
                    if self.focus==FOCUS_WHEEL: # Jump into the Wheel
                        self._col_index +=5
                        if self._col_index >= len(self._col):
                            self._col_index -= len(self._col)
                    else:
                        self.focus -= 1
                        
                elif _dir==ENTER:
                    if self.focus==FOCUS_WHEEL:
                        _key = self._col[self._col_index]
                        if self.is_printable(_key):
                            if self.fire_key_press(_key):
                                self.value += chr(_key)
                            else:
                                self.draw_msg( 'Refused!', 1000 )
                        elif _key==KEY_BS:
                            if len(self.value)>0:
                                self.value = self.value[:-1]
                        elif _key==KEY_SHIFT_IN:
                            self.set_state( STATE_SHIFTED )
                        elif _key==KEY_SHIFT_OUT:
                            self.set_state( STATE_NORMAL )
                        elif _key==KEY_SYMBOL:
                            self.set_state( STATE_SYMBOL )
                        elif _key==KEY_DIGIT:
                            self.set_state( STATE_DIGIT )
                    elif self.focus==FOCUS_CANCEL:
                        return False
                    elif self.focus==FOCUS_OK:
                        if self.fire_validate():
                            return True                               
                  
                # Redraw the screen
                self._refresh()
                time.sleep_ms(100)
                
                

