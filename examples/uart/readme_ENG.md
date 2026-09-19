[Ce fichier existe également en FRANCAIS](readme.md)

# Serial Monitor

The __[serial Monitor](serial-monitor)__ example is a small Arduino alike Serial Monitor linked to UART(0) with tx=GP0 and rx=GP1 .

![Serial Monitor introduction](serial-monitor/docs/serialmon-00.jpg)

More information on its dedicated [readme file](serial-monitor/readme.md).

# USB Serial Passthrough

The __[usb-serial](usb-serial)__ example allow to configure the UART setting via the menu THEN bring the CDC support (serial) on the USB with data transfert between the UART and USB-CDC.

![USB-Serial in action](usb-serial/docs/usbserial-1.jpg)

More information on its dedicated [readme file](usb-serial/readme.md) .

# dupterm

The __[uart-dupterm](uart-dupterm)__ example allow the user to configure the UART setting then replicates the REPL prompt on the UART. Once done, the script ends its execution. 

The can control the MicroPython plateform via the UART with a tool like Thonny, MPRemote, RShell or terminal software. 

![dupterm in action](dupterm/docs/dupterm-02.jpg)

More information in the [readme file](dupterm/readme.md) .