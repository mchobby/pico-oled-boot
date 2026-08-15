# OledEdit library

The [olededit.py](lib/olededit.py) script contains the __EditScreen__ class used to key-in alphanumeric user data with the Pico-Oled-Boot joystick.

The field editor encoding is kindly intuitive, the joystick is used to select the charactersLe (left/right), move the focus (up/down) and to confirm selection  (press). Note that using UP direction with the character whell do jump several letters at once.

![Working with field editor](docs/_static/oled-edit-00.jpg)

![Working with field editor](docs/_static/oled-edit-01.jpg)

![Working with field editor](docs/_static/oled-edit-03.jpg)

![Working with field editor](docs/_static/oled-edit-04.jpg)

![Working with field editor](docs/_static/oled-edit-05.jpg)

## Constants
The `STATE_xxx` constants are used to select the initial characters wheel at startup.
``` python
STATE_NORMAL = const(0) # Display normal char
STATE_SHIFTED= const(1) # Display Uppercase Char
STATE_DIGIT  = const(2) # Display Digit + Decimal_Separator
STATE_SYMBOL = const(3) # Displat @, #, (, ...
```

## EditScreen class

The __EditScreen__ class drives the display while capturing user data then returns to the callee when the data is comfirmed by the user.

![Working with the editor](docs/_static/oled-edit-00.jpg)

### Constructor

```
def __init__( self, oled_boot, label, initial_value='', on_key_press=None, on_validate=None, initial_state=STATE_NORMAL )
```

* __oled_boot__ : reference to the __OledBoot__ object (that herits from  __FrameBuffer__) giving access to the OLED display and various user input interface.
* __label__ : text displayed above the edit field.
* __initial_value__ : (optional) initial string value displayed into the edit field.
* __on_key_press__ : (optional) used to attach a callback event called just before its addition to the edit field. Can be used to reject selection when returning False. <br />Event(Owner,Key) where `owner` is the EditScreen instance and `key` the ASCII code of the added char.
* __on_validate__ : (optional) used to attach a callback event called before accepting the OK button. It is used to validate the input by returning True/False. The __ValueError__ exception are also captured and their message shown on the display for a second.<br />Event(value) where `value` contains the captured value.
* __initial_state__ : (optional, STATE_xxx constants) initial state of the character wheel. Allow the selection of an alternate wheel (like digits).

### Member value : string

Value captured by the user.

### Method show() : boolean

``` 
def show( self ):
```

Start data capture and return True/False depending on OK/Cancel user confirmation.

The captured value is available via the `value` attribute.

