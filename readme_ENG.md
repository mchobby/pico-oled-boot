[Ce fichier existe également en Français](readme.md)

# PICO-OLED-BOOT : all-in-one graphical controler for Pico (MicroPython compatible)

The PICO-OLED-Boot is a convenient tool to add a graphical display (OLED, 128x64px) together with controlers interfaces made of a joystick switch and buttons. 

Two LEDs are also available and can be used as user notification.

![PICO-OLED-BOOT](docs/_static/PICO-OLED-BOOT-00.jpg)

It also feature a Qwiic/StemmaQt connector and a reset button under the board for a quick and easy access. 

Thank to the GPIO expander, the full board can be controled with 4 pins. Two are used for I2C bus (gp6/gp7). The two other pins (gp2/gp3) are used for the buttons A & B in order allowing IRQ binding.

That leaves lots of remaining IO and buses for your own project.

![PICO-OLED-BOOT details](docs/_static/PICO-OLED-BOOT-05.jpg)

![PICO-OLED-BOOT](docs/_static/PICO-OLED-BOOT-06.jpg)

Software side includes everything you need to run it with MicroPython, an extra __menuboot__ library is available to __quickly implements menu__ with the product.

![MenuBoot on the Pico-Oled-Boot](docs/_static/PICO-OLED-BOOT-menu.jpg)

# Shopping list

* [Pico-Oled-Boot](https://shop.mchobby.be/fr/nouveaute/2914-pico-oled-boot-interface-oled-joystick-bouton-pour-raspberry-pi-pico-3232100029149.html) is available at MCHobby


# Schematic

The [schematic is also available here](docs/_static/pico-oled-boot-schematic.jpg)

# Library

The libraries must be copied on the MicroPython board before using the examples.

Absolute required libraries are:

* __oledboot__ : HELPER for using the board features.
* __menuboot__ : MENU drawing and handling.
* __olededit__ : data encoding screen.
* __sh1106__ : required for OLED screen
* __mcp230xx__ : required for joystick read

Those are installed with the package [pico-oled-boot/package.json](package.json) .

## Masters installation

The [masters.out/](masters.out) folder contains archive containing examples and libraries... everything is there!

You just need to copy the archive content on you MicroPython board while preserving the filesystem folder structure.

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


# Wire

Just plug your Pico onto the female header available on the back of the board. The board shows a __USB__ label on the silkscreen to indicates the orientation of the Pico (its USB connector must be oriented the same way)

# Examples 
The repository contains various examples script as first hand helper:

* __[test.py](examples/test.py)__ : test script used to check the board features (A/B/Start, Joystick, LEDs & OLED)
* __[games](examples/games/)__ : many games for your Pico-Oled-Boot<br />![jeu racer](examples/games/racer/docs/racer-01-lowres.jpg)
* __[RoboEyes examples](examples/roboeyes/)__ : using RoboEyes on the Pico-Oled-Boot<br />![RoboEyes sample](docs/_static/roboeyes.jpg)
* __[animation examples](examples/anim/)__ : animation can be displayed on the Pico-Oled-Boot< br/>See the [examples/anim/](examples/anim/) folder.
*  __[clock examples](examples/clock/)__ : various clock examples using the Pico-Oled-Boot display.<br />![Digital clock](docs/_static/clock_digital.jpg)
* __[i2c sensor examples](examples/i2c/)__ : Various examples displaying informations collected from I2C Sensor.<br />![BMP280/BME280 sensor connected on Qwiic/StemmaQT displaying their values](docs/_static/pico-oled-boot-bmp280.jpg)
* __[fonts (examples)](examples/fonts/)__ : Various examples showing how to use other fonts with yout Pico-Oled-Boot.
* __[menu examples](examples/menu/)__ : Menu features scripts examples<br />![OledMenu in action](docs/_static/menu-boot-01.jpg)
*  __[input examples](examples/input/)__ : Various input screen examples<br />![Field Editor](docs/_static/oled-edit-01.jpg)
* __[bootloader](examples/booloader/)__ : bootloader with autorun and selection menu  for starting script. Pres A to force menu display. Press B to skip autorun (go to REPL)<br />[See how it works!](examples/bootloader/docs/autorun-howto.jpg)<br />![bootloader menu in action](examples/bootloader/docs/autorun.jpg)

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

## Reading A & B buttons

As buttons are `Pin` instances, the values can be read with a `OledBoot.a.value()`. The advantages of the `Pin` is to attach a interrupt handler routine.

The following example attach IRQ routine to the buttons A & B then changes the user LED state each time the button is pressed.

```
from oledboot import *
import time
import micropython
micropython.alloc_emergency_exception_buf(100)

lcd = OledBoot()

# Using button A & B with IEQ
last_a = time.ticks_ms()
def a_pressed( pin ):
	global lcd, last_a
	# avoids two consecutive changes within 100ms
	if time.ticks_diff( time.ticks_ms(), last_a ) > 100:
		lcd.red.value( not(lcd.red.value()) )
		last_a = time.ticks_ms()

last_b = time.ticks_ms()
def b_pressed( pin ):
	global lcd, last_b
	if time.ticks_diff( time.ticks_ms(), last_b ) > 100:
		lcd.green.value( not(lcd.green.value()) )
		last_b = time.ticks_ms()

lcd.a.irq( handler=a_pressed, trigger=Pin.IRQ_RISING )
lcd.b.irq( handler=b_pressed, trigger=Pin.IRQ_RISING )
``` 

## Menu display

![Navigate the menu](boot/_static/menu-boot-nav.jpg)

See below the OledMenu library description (and file examples).

## User data acquisition

The code below is used to capture data with the __EditScreen__ class. The example script is available under the file [examples/test_input_screen.py](examples/test_input_screen.py) .

![Edit Screen](docs/_static/oled-edit-00.jpg)

See the following examples for data validation and numeric acquisition : [test_input_keypress.py](examples/test_input_keypress.py) and [test_input_validate.py](examples/test_input_validate.py)

``` python 
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
```

# OledBoot Library

The library is documented in the [doc-oledboot.md](doc-oledboot.md) file.

# MenuBoot Library

The library is documented in the [doc-menuboot.md](doc-menuboot.md) file.

The library also have demonstration scripts in the [examples/menu/](examples/menu/) folder.

# OledEdit Library

The library is documented in the [doc-menuboot.md](doc-menuboot.md) file.

The library also have demonstration scripts in the [examples/input/](examples/input/) folder.

# FBGFX library
Installed with the OledBoot library, the FBGFX library offers FrameBuffer based manipulation utilities as well as icons Libraries.

![FBGFX sample](docs/_static/fbgfx-sample.jpg)

## Fonts
The [examples/fonts/](examples/fonts/) scripts demonstrate the alternatives Fonts rendering.

![fbgfx fonts](docs/_static/fbgfx-fonts.jpg)

The library and its documentation are available on [esp8266-upy/FBGFX](https://github.com/mchobby/esp8266-upy/tree/master/FBGFX)

# RoboEyes Library
RoboEyes do use the FrameBuffer to draw and animate ayes on a display.

Roboyes for Pico-Oled-Boot do have examples scripts stored in the [examples/roboeyes/](examples/roboyeyes/) folder.

![RoboEyes sample](docs/_static/roboeyes.jpg)

The library and its documentation are available on [micropython-roboeyes](https://github.com/mchobby/micropython-roboeyes)

# Other useful libraries

* [FileFormat](https://github.com/mchobby/esp8266-upy/tree/master/FILEFORMAT) : to read image files.
* [COLORS](https://github.com/mchobby/esp8266-upy/tree/master/COLORS) : color manipulation utilities
* [ano-gui](https://github.com/peterhinch/micropython-nano-gui/tree/master) : a lightweight and minimal MicroPython GUI library from Peter-Hinch


