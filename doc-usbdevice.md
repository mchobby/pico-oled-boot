[This file also exists in ENGLISH](readme_ENG.md)

# Installer le support USB Device pour MicroPython

Quelques exemples nécessire le support USB Device avancé. Ce dernier est bâtit sur la classe `machine.USBDevice` .

___SI__ vous n'utilisez __PAS___ une archive mater pour installer votre Pico-Oled-Boot 

___ALORS___ le support USB Device avancé (usb core, usb CDC, etc) doit être installé par vos propres soins.

Les ressources sont disponible sur le dépôt [micropython-lib/usb-device](https://github.com/micropython/micropython-lib/tree/master/micropython/usb/usb-device/usb/device)

# Installation

## USB Core
Copier USB core dans `lib/usb/device/` de votre plateforme MicroPython:

* `__init__.py` est disponible [ici](https://raw.githubusercontent.com/micropython/micropython-lib/refs/heads/master/micropython/usb/usb-device/usb/device/__init__.py)
* `core.py` disponible [ici](https://raw.githubusercontent.com/micropython/micropython-lib/refs/heads/master/micropython/usb/usb-device/usb/device/core.py)
 
Voir [la page html](https://github.com/micropython/micropython-lib/tree/master/micropython/usb/usb-device/usb/device)

## USB CDC
Copier le support CDC vers `lib/usb/device/` :

* `cdc.py` est disponible [ici](https://raw.githubusercontent.com/micropython/micropython-lib/refs/heads/master/micropython/usb/usb-device-cdc/usb/device/cdc.py)

Voir [la page html](https://github.com/micropython/micropython-lib/blob/master/micropython/usb/usb-device-cdc/usb/device/cdc.py)