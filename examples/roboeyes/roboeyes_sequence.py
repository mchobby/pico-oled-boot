# RoboEyes animations 
# this example shows how to create Robo Eyes animation sequences without the use of delay(); 
#
# Hardware:
#    You'll need a breadboard, a Raspberry-Pi Pico, a FrameBuffer
#    based diplsay (like I2C SSD1306 oled and some jumper wires.
#
# See MicroPython implementation at 
#    https://github.com/mchobby/micropython-roboeyes
#
# Ported from Arduino https://github.com/FluxGarage/RoboEyes
#   Arduino example Published in September 2024 by Dennis Hoelscher, FluxGarage
#   www.youtube.com/@FluxGarage
#   www.fluxgarage.com
#
from oledboot import *
from roboeyes import *
import time

display = OledBoot()

# RoboEyes callback event
def robo_show( roboeyes ):
	global display
	display.show()

# Plug RoboEyes on any FrameBuffer descendant
robo = RoboEyes( display, 128, 64, frame_rate=100, on_show = robo_show )

# Give a second to the eyes to open
start = time.ticks_ms()
while time.ticks_diff( time.ticks_ms(), start ) < 1000 :
	robo.update()  

# RoboEyes can store several animation sequences 
#   Lets create the sequence ZERO
seq = robo.sequences.add( "demo" )
seq.step( 2000, lambda robo : robo.open() ) # at 2000 ms from start --> open eyes.
seq.step( 4000, lambda robo : robo.set_mood(HAPPY) ) # Lamba must call function! Cannot assign property! 
seq.step( 4010, lambda robo : robo.laugh() )
seq.step( 6000, lambda robo : robo.set_mood(TIRED) )
seq.step( 8000, lambda robo : robo.set_mood(DEFAULT) )
seq.step( 9000, lambda robo : robo.close() )
seq.step( 10000, lambda robo : print(seq.name,"done !") )  # Also signal the end of sequence at 10 sec


# RoboEyes Initial state
robo.position = DEFAULT
robo.close()

# Start the sequence ZERO
robo.sequences[0].start()

while True:
	# update eyes drawings
	robo.update()  

	# if robo.sequences.done: # Check all sequences done
	if robo.sequences[0].done: # Check sequence ZERO done
		# Restart a sequence
		robo.sequences[0].reset()
		robo.sequences[0].start()

	# Dont' use sleep() or sleep_ms() here in order to ensure fluid eyes animations.
 	# Check the AnimationSequences example for common practices.
