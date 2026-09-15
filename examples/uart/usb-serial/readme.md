# USB-Serial Pass-Through

The [UsbSerial.py](usbserial.py) example establish a passthrough connexion between the USB port and the UART(0) on GP0=tx and GP1=rx.

UART(0) can be configured in baudrate, data bits, parity, stop bits thank to the menu (Press A button to bring up the menu)

![USB Serial introduction screen](docs/usbserial-0.jpg)

Once started, the script display a statistic screen showing the bytes transfered in each direction.

![USB Serial screen](docs/usbserial-1.jpg)

Statistics can be reset at any moment by pressing the "Start" button.

__Important Note:__

The USB connexion get reset when the script initialise the USBDevice layer.

# Library

Running this examples requires the __Advanced USB Device__ support to be installed.

The installation is described in this [USBDevice install documentation](../../doc-usbdevice_ENG) .

