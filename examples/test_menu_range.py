""" MicroPython Menu for PICO-OLED-BOOT - Basic example

   This example show how to:
	* add Range  MenuItem
        * detect the Range value change
        * read the selected value

See project https://github.com/mchobby/pico-oled-boot 

domeu, 9 march 2026, Initial Writing (shop.mchobby.be) """

from oledboot import *
from menuboot import *

lcd = OledBoot()
menu = MenuBoot( lcd )

# code, Label
menu.add_label( "t1", "test1" ) # code, Label
menu.add_range( "preheat" , "PreHeat %s C", 25, 180, 5, 50 ) # Min, Max, Step, default
menu.add_label( "t2", "test2" ) # code, Label
menu.add_label( "get", "Get preheat" ) # code, Label
menu.add_label( "t4", "test4" ) # code, Label
menu.add_label( "t5", "test5" ) # code, Label
menu.add_label( "t6", "test6" ) # code, Label
menu.add_label( "t7", "test7" ) # code, Label
menu.add_label( "t8", "test8" ) # code, Label

menu.start()

while True:
	if menu.update(): # true when entry selected
		entry = menu.selected # will reset selection
		if entry:
			print( "%s selected" % entry )

			if entry.code=="preheat":
				print( "Preheat changed!" )
				print( "Preheat= %s" % entry.cargo.value )

			if entry.code=="get":
				print( "Lets retreives PreHeat value..." )
				print( "Preheat= %s" % menu.by_code("preheat").cargo.value )
	# Process other tasks here
