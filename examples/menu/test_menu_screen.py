""" MicroPython Menu for PICO-OLED-BOOT - Custom Screen display

   This example show how to draw your own MenuItem applet 
   (the "screen" content behind a MenuItem). See the code 
   attached to "dashboard" to understand how the screen is 
   displayed. 
   Screen is displayed until the Enter key is pressed again.
   After the Screen display operation, the menu automatically 
   reappears in its previous state.

See project https://github.com/mchobby/pico-oled-boot 

domeu, 9 march 2026, Initial Writing (shop.mchobby.be) """
import time
from oledboot import *
from menuboot import MenuBoot

lcd = OledBoot()
menu = MenuBoot( lcd )

# Callback to draw screen/dashboard
#
start = None
def on_dash_start( ctrl ):
	# Start is used to initialize
	global start
	start = time.ticks_ms()

def on_dash_draw( ctrl, oled ): # ScreenControler, Oled Screen, Encoder
	global start
	oled.fill( 0 )
	oled.text( "%i" % int(time.ticks_diff( time.ticks_ms(),start )) , 5, 20, 1 )
	oled.show() # update screen

# code, Label
menu.add_label( "start", "Start Oven" )
menu.add_range( "preheat" , "PreHeat %s C", 25, 180, 5, 50 ) # Min, Max, Step, default
menu.add_screen( "scr1", "Dashboard", on_dash_draw, on_dash_start ) # code, Label and optional "cargo object"

menu.start()

while True:
	if menu.update(): # true when entry selected
		entry = menu.selected # will reset selection
		if entry:
			print( "%s selected" % entry )

		# The screen is diplayed and managed by the menu.
		# Nevertheless, we are informed when the screen have
		# been displayed.
		if entry and entry.code=="scr1":
			print( "%s has been showed" % entry.code )

	# Process other tasks here
