from machine import Pin

# Reset Red & Green LEDS
i2c = I2C(  1, sda=Pin(6), scl=Pin(7), freq=400000 )
mcp = MCP23008( i2c=i2c, address=0x26 )
mcp.setup( 5, Pin.OUT )
mcp.setup( 6, Pin.OUT ) # RED
mcp.output_pins( {6: False, 5: False} )

btn_b = Pin(2, Pin.IN, Pin.PULL_UP)

# B not pressed? => Load autorun
if btn_b.value():
	from oledboot import OledBoot
	lcd = OledBoot()
	lcd.fill(0)
	lcd.show()
	try:
		from autorun import module
		print( 'main.py: start module', module)
		lcd.text('Starting module',0,0)
		lcd.text(module,0,12)
		lcd.show()
		time.sleep_ms(500)
		__import__(module)
	except Exception as err:
		lcd.fill(0)
		s = '%s'%err
		for i in range(9):
			lcd.text( s[16*i:16*(i+1)], 0, 8*i )
		lcd.show()
		while True:
			mcp.output_pins( {6:True} )
			time.sleep_ms( 50 )
			mcp.output_pins( {6:False} )
			time.sleep_ms( 50 )		
else:
	print( 'main.py: skip execution')
	mcp.output_pins( {6: True} ) # RED