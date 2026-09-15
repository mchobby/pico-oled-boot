[Ce fichier existe également en FRANCAIS](readme.md)

# Install the USB Device support for MicroPython

Some of the software require Advanced USB Device support. this one is built on the top of `machine.USBDevice` .

___IF NOT___ using MASTERs archive to install your Pico-Oled-Boot 

___THEN___ Advanced USB Device (usb core, usb CDC, etc) must be installed by your own mean.

The ressources is availables at [micropython-lib/usb-device](https://github.com/micropython/micropython-lib/tree/master/micropython/usb/usb-device/usb/device)

# Install

## USB Core
Copy the USB core to `lib/usb/device/` :

* `__init__.py` available [here](https://raw.githubusercontent.com/micropython/micropython-lib/refs/heads/master/micropython/usb/usb-device/usb/device/__init__.py)
* `core.py` available [here](https://raw.githubusercontent.com/micropython/micropython-lib/refs/heads/master/micropython/usb/usb-device/usb/device/core.py)
 
See [html link](https://github.com/micropython/micropython-lib/tree/master/micropython/usb/usb-device/usb/device)

## USB CDC
Copy the USB CDC to `lib/usb/device/` :

* `cdc.py` available [here](https://raw.githubusercontent.com/micropython/micropython-lib/refs/heads/master/micropython/usb/usb-device-cdc/usb/device/cdc.py)

see [html link](https://github.com/micropython/micropython-lib/blob/master/micropython/usb/usb-device-cdc/usb/device/cdc.py)