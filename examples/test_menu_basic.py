""" MicroPython Menu for PICO-OLED-BOOT - Basic example

   This example show how to:
	* Define a menu with Menu Entries
        * add simple MenuItem
	* add Range  MenuItem
        * detect the selected menu entry
        * enable/disable MenuItem

See project https://github.com/mchobby/pico-oled-boot 

domeu, 9 march 2026, Initial Writing (shop.mchobby.be) """

from oledboot import *
from menuboot import *

lcd = OledBoot()
menu = MenuBoot( lcd )

# code, Label
menu.add_label( "start", "Start Oven" )
menu.add_label( "stop" , "Stop Oven" , enabled=False )
menu.add_range( "preheat" , "PreHeat %s C", 25, 180, 5, 50 ) # Min, Max, Step, default
menu.add_label( "t1", "test1" ) # code, Label
menu.add_label( "t2", "test2" ) # code, Label
menu.add_label( "t3", "test3" ) # code, Label
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

			if entry.code=="start":
				menu.by_code("stop").enabled=True
			elif entry.code=="stop":
				menu.by_code("stop").enabled=False
	# Process other tasks here
