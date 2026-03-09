[Ce fichier existe également en Français](readme.md)

# PICO-OLED-BOOT : all-in-one graphical controler for Pico (MicroPython compatible)

The PICO-OLED-Boot is a convenient tool to add a graphical display (OLED, 128x64px) together with controlers interfaces made of a joystick switch and buttons. Two LEDs are also available and can be used as user notification.

![PICO-OLED-BOOT](docs/_static/PICO-OLED-BOOT-00.jpg)

It also feature a Qwiic/StemmaQt connector and a reset button under the board for a quick and easy access. 

Thank to the GPIO expander, the full board can be controled with 4 pins. Two are used for I2C bus (gp6/gp7). The two other pins (gp2/gp3) are used for the buttons A & B in order allowing IRQ binding.

That leaves lots of remaining IO and buses for your own project.

![PICO-OLED-BOOT details](docs/_static/PICO-OLED-BOOT-05.jpg)

![PICO-OLED-BOOT](docs/_static/PICO-OLED-BOOT-06.jpg)

The [schematic is also available here](docs/_static/pico-oled-boot-schematic.jpg)

# Library

The libraries must be copied on the MicroPython board before using the examples.

Absolute required libraries are:

* oledboot : helper for using the board features.
* sh1106 : required for OLED screen
* mcp230xx : required for joystick read


## Install with MPRemote

On a WiFi capable plateform:

```
>>> import mip
>>> mip.install("github:mchobby/pico-oled-boot")
```

Or via the mpremote utility :

```
mpremote mip install github:mchobby/pico-oled-boot
```

## Manual install

You can check the [package.json](package.json) file to locate the various libraries then copy the required files to your micropython board.

# Wire

Just plug your Pico onto the female header available on the back of the board. The board shows a __USB__ label on the silkscreen to indicates the orientation of the Pico (its USB connector must be oriented the same way)

# Test

## Reading directions
The following script reads the joystick switch and Start button then displays it corresponding text label on the OLED.

```
from oledboot import *
import time
import micropython
micropython.alloc_emergency_exception_buf(100)

labels = {START:"Start", ENTER:"Enter", UP:"Up", DOWN:"Down", LEFT:"Left", RIGHT:"Right"}
lcd = OledBoot()
# Initialize screen
lcd.fill(0)
lcd.show()

while True:
	lcd.fill(0) # Clear
	_d = lcd.dir # Get direction
	if _d in labels:
		lcd.text( labels[_d],0,0,1 ) # Text,x,y,color
	elif _d > 0: # 0=No direction
		lcd.text( str(_d), 0,0, 1 )
	lcd.show()
	time.sleep_ms( 100 )
```

Note: `dir` returns 0 when nothing is detected. When a combination of buttons (UP + Start) is detected then their constants are summed together. In this case, the numeric value is displayed instead of labels combinations.

Remarks: 

1. a proper detection can be made with expression like `(dir and RETURN)== RETURN`
2. each access to `dir` property issues a communication over the I2C bus. A better approach is to copy the `dir`  result in the local variable.

# oledboot library

The [oledboot.py](lib/oledboot.py) file contains the __OledBoot__ class as well as the required constant definition.

Only the essential definitions are listed below.

## Constants

The following constant are used to identify the direction of the joystick. The constants also cover the "Start" button as well as the "Enter" key (when joystick is pressed down).

```
DOWN = const(1)
UP   = const(8)
RIGHT= const(4)
LEFT = const(16)
ENTER= const(2)
START= const(32)
```

Note that going up while pressing the joystick will returnns the value ENNTER+UP (so 10). The value 0 will be returned when no direction is selected.

## OledBoot class

The __OledBoot__ class will offer a quick access to screen, input and outputs. The class takes care of allocating the required ressources.

The __OledBoot__ inherits from [MicroPython FrameBuffer](https://docs.micropython.org/en/latest/library/framebuf.html) so you can call all known drawing primitives (see [documentation here](https://docs.micropython.org/en/latest/library/framebuf.html))

Remark:

The FBGFX library (also installed with MPRemote) can be used to expand the capabilities of the FrameBuffer. Check the [FBGFX documentation here](https://github.com/mchobby/esp8266-upy/tree/master/FBGFX))

### Constructor

``` 
def __init__( self, oled_addr=0x3c, mcp_addr=0x26 )
```

* __oled_addr__ : I2C address of the OLED screen. This can be change to an alternative address on the back of the display. In such case, indicates the new address in this parameter.
* __mcp_addr__ : I2C address of the GPIO expander. That address can be changed in the back of the PCB on a 3 points solder jumper (cut the current trace and solder the opposite one to the center pole ). Indicates the new I2C address here when changed.

### member i2c : I2C

Provide access to the I2C bus shared between the OLED screen, GPIO expander and Qwiic port.

This reference will be useful when connecting extra device on the Qwiic port.

### members a: Pin , b: Pin

Gives access to the A or B buttons. As they are instances of Pin class, user code can access the `value()` method or attach an IRQ handler.

Reading the value return `False` when the button is pressed and `True` when released.

### Members red: LedAdapter, green: LedAdapter

Gives access to the "green" and "red" leds above the joystick.

The LedAdapter class offers the methods `value()`, `on()` and `off()` allowing to control the LEDs as simple `Pin` class.

### Member dir: int

Check the current state of the joystick (and Start button) then returns one of the constants DOWN, UP, RIGHT, LEFT, ENTER, START otherwise 0.

Note that several action can be combined like RIGHT+START or LEFT+START+ENTER. In such case, the innvolved constant value are sum.

## LedAdapter class

The __LedAdapter__ class is designed to control the both LED on the GPIO expander (MCP23008) as it was simple Pin class. So the class expose the methodes:

* __on()__ : activates the LED
* __off()__ : deactivates the LED
* __value()__ : use the boolean parameter to set/unset the LED state. Without parameter, it returns the last known value.

# FBGFX library
Installed with the OledBoot library, the FBGFX library offers FrameBuffer based manipulation utilities as well as icons Library

![FBGFX sample](docs/_static/fbgfx-sample.jpg)

# Other useful libraries

* [micropython-roboeyes](https://github.com/mchobby/micropython-roboeyes) : library draws smoothly animated robot eyes on OLED displays.
* [Small-Font](https://github.com/mchobby/esp8266-upy/tree/master/SMALL-FONT) a smaller font for MicroPython
* [FileFormat](https://github.com/mchobby/esp8266-upy/tree/master/FILEFORMAT) : to read image files.
* [COLORS](https://github.com/mchobby/esp8266-upy/tree/master/COLORS) : color manipulation utilities
* [ano-gui](https://github.com/peterhinch/micropython-nano-gui/tree/master) : a lightweight and minimal MicroPython GUI library from Peter-Hinch

# Shopping list

* [Pico-Oled-Boot](https://shop.mchobby.be/fr/nouveaute/2914-pico-oled-boot-interface-oled-joystick-bouton-pour-raspberry-pi-pico-3232100029149.html) is available at MCHobby