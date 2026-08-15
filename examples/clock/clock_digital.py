# Clock-Digital.py : Display a digital clock
#
from oledboot import *
from fbtext import *
from digit24x24 import Font24X24 as Digit24X24
from font14x14 import Font14X14
from font8x4 import Font8X4
from machine import RTC, I2C, Pin
import time, sys

mcu_rtc = RTC()
lcd = OledBoot()

# Try to detect External RTC
error_msg = None
addrs = lcd.i2c.scan()

# PCF8523 doesnt always enumerate on i2c.scan()
# So try to mount it the brutal way
try:
	from pcf8523 import PCF8523
	ext_rtc = PCF8523(lcd.i2c)
	print( 'PCF8523 datetime :', ext_rtc.datetime )
	mcu_rtc.datetime( ext_rtc.datetime )
except Exception as err:
	error_msg = ['PCF8523 RTC init failed!', '%s' % err ]


WAIT_TIME = 5
if not error_msg is None:
	lcd.fill(0)
	lcd.text(error_msg[0][ 0:16], 0, 0, 1 )
	lcd.text(error_msg[0][16:32], 0, 10, 1 )
	lcd.hline( 0,22, lcd.width, 1 )
	lcd.text(error_msg[1][ 0:16], 0, 25, 1 )
	lcd.text(error_msg[1][16:32], 0, 35, 1 )	
	lcd.text(error_msg[1][32:48], 0, 45, 1 )
	for i in range( WAIT_TIME, 0, -1 ):
		print( i )
		lcd.fill_rect( 0,  lcd.height-8, lcd.width, 8, 0 )
		lcd.text('Wait %i sec' % i, 0, lcd.height-8, 1 )
		lcd.show()	
		time.sleep( 1 )
	

# Current Language FR/ENG 
LANG = "FR"

# Day of the Week 0..6 for Monday..Sun 
WEEK_DAY = {"ENG" : ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
            "FR"  : ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"] } 

# Month Name from January (1) to December (12) 
MONTH_NAME = {"ENG" : ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
			  "FR"  : ["Jan","Fev","Mar","Avr","Mai","Jun","Jul","Aou","Sep","Oct","Nov","Dec"] }

MOON_PHASE_TEXT = {"ENG" : "Moon  Phase",
				   "FR"  : "Phase  Lunaire"}

# Last known "New Moon" for reference
NEW_MOON_REF = (2026, 7, 14, 0, 0, 0, 0, 0) #yy,mm,dd,hh,nn,ss,week_day,year_day
moon_ref_sec = time.mktime( NEW_MOON_REF )

hh_drawer = FBText( lcd, lcd.width, lcd.height, Digit24X24() )
ss_drawer = FBText( lcd, lcd.width, lcd.height, Font14X14() )
text_drawer= FBText( lcd, lcd.width, lcd.height, Font8X4() )

def day_name( week_day ):
	if not LANG in WEEK_DAY:
		return '???'
	if not 0<=week_day<len(WEEK_DAY[LANG]):
		return '???' 
	return WEEK_DAY[LANG][week_day]

def month_name( month ):
	if not LANG in WEEK_DAY:
		return '???'
	if not 1<=month<=len(MONTH_NAME[LANG]):
		return '???' 
	return MONTH_NAME[LANG][month-1]

def moon_phase_filling( phase_pc ):
	# Returns tuple (filling, quadrant)
	#   filling 0..1, 
	#   quadrant 1..2 (1=fill from right, 2=fill from left)
	# Results in the following progression
	#     +------ Fill from right -------------+       +----- Unfill to Left -------+
	#   (0,0), (0.25,0), (0.50,0), (0.75,0), (1,0), (0.75,1), (0.50,1), (0.25,1), (0,1)
	return 1-abs((phase_pc-50)/50), 0 if phase_pc<=50 else 1

# Moon Phase Label
#   We want to accomodate letter color to the background color
#   For that we must deal directly with Font feature
_mp_label_w = text_drawer.font.text_width( MOON_PHASE_TEXT[LANG] )
_mp_x = (lcd.width-_mp_label_w)//2
# store x position of each letter!
__mp_chars = []
__sum = 0
for c in MOON_PHASE_TEXT[LANG]:
	__mp_chars.append( (c, _mp_x+__sum) )
	__sum += (text_drawer.font.char_width(text_drawer.font.char_index(c))+text_drawer.font.gutter_space )


while True:
	lcd.fill(0) # Clear

	# Get Date Time
	y,m,d,wd,hh,mm,ss,ms = mcu_rtc.datetime()

	# Moon phase from New Moon --> during 29.53 days
	#  New Moon = Black
	#  Lighting from extrem right in clockwise direction
	#  At 29.53/4 days Half moon is lit (right)
	#  At 29.53/2 days Full moon is lit 
	#  At 29.53*3/4 days Half monn is lit (left)
	#  At 29.53 days all moon is dark


	# Calculate the Moon Phase
	#   Delta in days % 29.53
	moon_age = ((time.mktime( (y,m,d,hh,mm,ss,0,0) )-moon_ref_sec)/(24*3600)) % 29.53
	# Moon phyase in percent (0..100 pc) for (0..29.53 days)
	moon_phase = moon_age / 29.53 *100
	# filling 0..1, quadrant 1..2 (1=fill from right, 2=fill from left)
	# Progression +------ Fill from right -----------------+  +------- Unfill to Left ----------+
	# Progression (0,0), (0.25,0), (0.50,0), (0.75,0), (1,0), (0.75,1), (0.50,1), (0.25,1), (0,1)
	moon_fill, moon_quadrant = moon_phase_filling(moon_phase)	
	print( "Moon phase", moon_phase, "fill",moon_fill,"Quad",moon_quadrant )
	w = lcd.width-12-1 # Progress width
	lcd.ellipse(6,6,6,6,1) #x,y,xr,yr, color, fill, quadrant_bits
	lcd.ellipse(lcd.width-6-1,6,6,6,1) #x,y,xr,yr, color, fill, quadrant_bits
	lcd.hline(7, 0,w,1 )
	lcd.hline(7,12,w,1 )
	if moon_quadrant==0: # Fill from right ro left
		wh_from_rel  = w-int(w * moon_fill) # White_from_relative
		wh_width     = int(w * moon_fill)
		bl_from_rel  = 0
		bl_width     = wh_from_rel-1
	else:
		wh_from_rel  = 0
		wh_width     = int(w * moon_fill) # White_from_relative
		bl_from_rel  = wh_width+1
		bl_width     = w-wh_width-1
	lcd.fill_rect(7+wh_from_rel,1,wh_width,11,1) # Fill white part
	lcd.fill_rect( 7+bl_from_rel,1,bl_width,11,0 )

	# --- Moon Phase (text) ---
	#text_drawer.text( "Moon  phase", 64-16, 2, 1 )
	for c,x in __mp_chars:
		_color =0
		if moon_quadrant==0:
			__color = x<(7+bl_width)
		else:
			__color = x>(7+wh_width)
		text_drawer.text( c, x, 2, __color )


	# --- Draw time ---
	stime="%02i:%02i" % (hh,mm)
	hh_drawer.text( stime, 2, (lcd.height-hh_drawer.font.h)//2-3, 1 ) # Text,x,y,color
	ssec="%02i" % (ss,)
	ss_drawer.text( ssec, 105, (lcd.height-hh_drawer.font.h)//2-3, 1 ) # Text,x,y,color
	
	# --- Draw Day ---
	sday = "%3s%3s" % (day_name(wd), d)
	ss_drawer.text( sday, 2 , lcd.height-ss_drawer.font.h-4, 1 ) # Text,x,y,color

	# --- Draw Date ---
	sdate = "%3s   %4i" % ( month_name(m),y)
	text_drawer.text( sdate,75, lcd.height-text_drawer.font.h-4, 1 )


	lcd.show()
	time.sleep_ms( 20 )

