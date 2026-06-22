from oledboot import *
from menuboot import *
import os, time

EMPTY = 'Empty!'

lcd = OledBoot()
menu = MenuBoot( lcd )

l = os.listdir()
for name in l:
	if name in ('boot.py','main.py','autorun.py','pyselect.py'):
		continue
	if '.py' in name:
		label = name.replace('.py','')
		menu.add_label( label, label )
if len(menu.items)==0:
	menu.add_label( EMPTY, EMPTY )

menu.start()

while True:
	if menu.update(): # true when entry selected
		entry = menu.selected # will reset selection
		if entry==EMPTY:
			continue
		else:
			print( "bootmenu.py: %s selected" % entry.code)
			f = open( 'autorun.py', 'w')
			f.write( 'module="%s"\n' % entry.code )
			f.close()
			time.sleep_ms( 500 )
			from machine import soft_reset
			soft_reset()
