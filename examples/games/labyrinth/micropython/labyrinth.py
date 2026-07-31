# Labyrinth game running a given level (designed with Tiled)
#
# Hardware Requirement:
# - Pico-Oled-Boot
# - Buzzer wired to GP16
#
from micropython import const
from oledboot import *
from fbutil import FBUtil
from img import open_image
from framebuf import FrameBuffer, MONO_HLSB
from sys import exit
from maps import slice_by 
import json, time, random

random.seed( machine.ADC(machine.Pin(28)).read_u16() )

PIN_BUZZER = const(16)

BTN_A = 100
BTN_B = 101


CURSOR_BLINK_MS = const(500) # Player Cursor Blink
CURSOR_MOVE_MS  = const(150) # Player Cursor movement capture 
ERROR_MS        = const(1500)
BUTTON_MS       = const(500) # Minimum time between button events detection
CHRONO_TIME_MS  = const(20000)
MESSAGE_MS      = const(5000) # Popup Message
HEALTH_IMMUNE_MS= const(1000) # Time during which the second hurt cannot impact player.

ERROR_TILE_ID   = const(159)
PLAYER_TILE_ID  = const(154)
FLAG_TILE_ID    = const(137)
KEY_TILE_ID     = const(95)
CHRONO_TILE_ID  = const(116) # allow crossing closed door
TELEPORT_1_TILE_ID = const(85)
TELEPORT_2_TILE_ID = const(105)
FIRST_AID_TILE_ID  = const(139)

OBJECT_TYPE_POEPLE = const(1)
OBJECT_TYPE_OBJECT = const(2)
OBJECT_TYPE_ACTION = const(3)
OBJECT_TYPE_DOOR   = const(4)

SCREEN_GAMEBOARD   = const(1)
SCREEN_MAP         = const(2)
SCREEN_INVENTORY   = const(3)

class EventTimeout:
	# __slot__ = ('state','expire_ms')
	def __init__( self ):
		self.state = None
		self.expire_ms = time.ticks_ms()

	@property
	def expired( self ):
		return time.ticks_ms() > self.expire_ms

	@property
	def remain( self ):
		return time.ticks_diff( self.expire_ms, time.ticks_ms() ) 

	def set( self, state, delay_ms ):
		# Set the new state that will expires in delay_ms
		self.state = state
		self.expire_ms = time.ticks_add( time.ticks_ms(), delay_ms )


class Coord:
	__slot__ = ('x','y')

	def __init__( self, x=None, y=None ):
		if x!=None:
			self.x = x
		if y!=None:
			self.y = y

	def set( self, pos ):
		assert isinstance( pos, Coord )
		self.x = pos.x
		self.y = pos.y

	def __repr__( self ):
		return "<%s %i, %i>" % (self.__class__.__name__, self.x, self.y)


class Inventory( dict ):
	# Maintain the quantity of tile objects collected by the player
	def add_object( self, tile_id ):
		if tile_id in self:
			self[tile_id] = self[tile_id] + 1
		else:
			self[tile_id] = 1
		print( 'add_object', tile_id, self[tile_id])

	def remove_object( self, tile_id ):
		if tile_id in self:
			self[tile_id] = self[tile_id] - 1
			if self[tile_id] < 0:
				self[tile_id] = 0
			print( 'remove_object', tile_id, self[tile_id])

	def count_of( self, tile_id ):
		if tile_id in self:
			print( 'count_of', tile_id, self[tile_id])
			return self[tile_id]
		return 0


class Player:
	def __init__( self, tile_w, tile_h ): # Size of tile
		self.tile_w = tile_w
		self.tile_h = tile_h
		self.pos    = Coord(0,0) # Position in Tile unit
		self.health = 100
		self.inventory = Inventory()

	def set( self, xtile, ytile ):
		# Set the user position in tile
		self.xtile = xtile
		self.ytile = ytile

	def x( self ):
		# Position of the player in pixel (top-left)
		return self.pos.x * self.tile_w

	def y( self ):
		return self.pos.y * self.tile_h

class Tile( FrameBuffer ):
	__slots__ = ['buf']
	def __init__( self, tile_width, tile_height ):
		self.buf = bytearray( tile_height*((tile_width//8)+(0 if (tile_width%8)==0 else 1 )) )
		super().__init__( self.buf, tile_width, tile_height, MONO_HLSB )


class TileSet( dict ):
	""" Collection of tile """
	def __init__( self, tile_width, tile_height ):
		self.tile_width = tile_width
		self.tile_height = tile_height
		super().__init__()

	def load_from( self, filename, id_list ):
		# id_list is a list of tile_id 
		reader = open_image( filename )
		tiles_per_line = reader.reader.width // self.tile_width # in pixel

		for tile_id in id_list:
			tile_row = tile_id//tiles_per_line
			tile_col = tile_id%tiles_per_line

			reader.clip( 0+tile_col*self.tile_width, 0+tile_row*self.tile_height, self.tile_width, self.tile_height )
			# Copy the clipped aread TO a target FrameBuffer (lcd) at is starting
			# position 0,0 for the given clipping width,height .
			_tile = Tile( self.tile_width, self.tile_height )
			#reader.copy_to(_tile, 0,0, lambda rgb : 1 if rgb==(255,255,255) else 0 ) 
			reader.copy_fast_to(_tile, 0,0 ) 
			# Append the tile to the collection
			self[tile_id] = _tile			


class GameObject:
	# An object in the game
	__slot__ = ('visible','x','y','tile_id','tile','cargo')
	def __init__(self, x_tile, y_tile, tile_id, tileset, **kwarg ):
		# Tileset reference is used to find a reference to the FremaBuffer tile
		self.x_tile  = x_tile
		self.y_tile  = y_tile
		self.tile_id = tile_id # Identification of the tile
		self.tile    = tileset[tile_id]
		self.cargo   = None # useful reference for descendant object
		self.visible = True

	def __repr__( self ):
		return "<%s %i,%i tile_id=%i visible=%s" % (self.__class__.__name__, self.x_tile, self.y_tile, self.tile_id, self.visible ) 

class DoorObject( GameObject ):
	# Doors are GameObject with state (open or closed)
	def __init__(self, x_tile, y_tile, tile_id, tileset, **kwarg ):
		# Tileset reference is used to find a reference to the FremaBuffer tile
		# * tile_id : is the closed door
		# * openned_id : (kwarg) is the openned door
		# * state : (kwarg) is the current state (1=open/0=close)
		super().__init__( x_tile, y_tile, tile_id, tileset, **kwarg )
		# Openned_id, Open_Tile, State
		self.cargo=[kwarg['openned_id'],tileset[kwarg['openned_id']],kwarg['state']] 

	@property
	def state( self ):
		# state of the door (1=open, 0:close)
		return self.cargo[2] 

	@state.setter
	def state( self, value ):
		self.cargo[2] = 1 if value else 0

	@property
	def door_tile( self ):
		# Return the appropriate tile reference accordingly to the door state
		if self.cargo[2]:
			return self.cargo[1]
		else:
			return self.tile

	@property
	def close_tile( self ):
		return self.tile

	@property
	def open_tile( self ):
		return self.cargo[1]

	def __repr__( self ):
		return "<%s %i,%i closed_id=%i openned_id=%i state=%i visible=%s>" % (self.__class__.__name__, self.x_tile, self.y_tile, self.tile_id, self.cargo[0], self.cargo[2], self.visible ) 


class GameObjectList( list ):
	def __init__(self,object_type, tileset, itemclass=GameObject ):
		assert object_type in (OBJECT_TYPE_POEPLE, OBJECT_TYPE_OBJECT, OBJECT_TYPE_ACTION, OBJECT_TYPE_DOOR ), "Invalid object_type %i" % object_type
		self._itemclass = itemclass
		self.object_type = object_type
		self.tileset = tileset
		self._k = {} # dictionnary for quick retreive on key (x*1000+y)
		super().__init__()

	def add_object( self, x_tile, y_tile, tile_id, **kwarg ):
		_r = self._itemclass(x_tile, y_tile, tile_id, self.tileset, **kwarg )
		self.append( _r )
		# Use a dictionnary for quick retreival
		self._k[ x_tile*1000+y_tile ] = _r

	def in_area( self, x_tile, y_tile, w_tile, h_tile ):
		# List of visible object inside the defined area
		_r = []
		for obj in self:
			if (x_tile <= obj.x_tile < x_tile+w_tile) and (y_tile <= obj.y_tile < y_tile+h_tile) and obj.visible:
				_r.append( obj )
		return _r

	def get_object( self, x_tile, y_tile ):
		key = x_tile*1000+y_tile
		if key in self._k:
			return self._k[key]
		return None


class LevelInfo:
	def __init__( self, level_name ):
		self.config = json.load( open('%s.json' % level_name) ) # This is a dictionnary
		self.width = self.config['width'] # Size in tile
		self.height = self.config['height'] # size in tile
		self.tile_width =  self.config['tilewidth'] # Size in tile
		self.tile_height =  self.config['tileheight'] # Size in tile
		self.tileset = TileSet( self.tile_width, self.tile_height )
		# Collect the IDs to load from TileSet
		_tile_ids = [ERROR_TILE_ID]
		for col_name in ( 'poeple','action','object' ):			
			for x,y,tile_id in self.config[col_name]:
				if not( tile_id in _tile_ids ):
					_tile_ids.append( tile_id )
		for x,y,closed_id,openned_id,state in self.config['door']:
			if not(closed_id) in _tile_ids:
				_tile_ids.append( closed_id )
			if not(openned_id) in _tile_ids:
				_tile_ids.append( openned_id )
		# print( _tile_ids )
		self.tileset.load_from( 'tileset.pbm', _tile_ids ) # [self.level.player_tile_id, self.level.flag_tile_id, ERROR_TILE_ID] )

		self.poeples = GameObjectList( OBJECT_TYPE_POEPLE, self.tileset )
		self.actions = GameObjectList( OBJECT_TYPE_ACTION, self.tileset )
		self.objects = GameObjectList( OBJECT_TYPE_OBJECT, self.tileset )
		# Create the door objects list
		self.doors   = GameObjectList( OBJECT_TYPE_DOOR  , self.tileset, itemclass=DoorObject )		

		with open( '%s.wall' % level_name, 'rb' ) as f:			
			self._wall_buf = bytearray( (self.width//8 + (0 if self.width%8==0 else 1))*self.height )
			f.readinto(self._wall_buf) # read all binary data (bit for tile)
			self.wall = FrameBuffer( self._wall_buf, self.width, self.height, MONO_HLSB )

		self.initial_player_pos = None		
		# find Position for player and flag
		for xtile, ytile, tile_id in self.config['poeple']:
			if tile_id == PLAYER_TILE_ID:
				self.initial_player_pos = Coord(xtile,ytile) # but doesn't register it as poeple to display
			else:
				# ready to use poeple collection
				self.poeples.add_object( xtile, ytile, tile_id )
		if self.initial_player_pos==None:
			raise Exception( 'Initial player position (tile_id=%i) missing in poeple collection!' % PLAYER_TILE_ID )

		# Create a ready to use actions & objects collection
		for xtile, ytile, tile_id in self.config['action']:
			self.actions.add_object( xtile, ytile, tile_id )
		for xtile, ytile, tile_id in self.config['object']:
			self.objects.add_object( xtile, ytile, tile_id )
		# Create the ready to use doors object collection
		for xtile, ytile, close_tile_id, open_tile_id, state in self.config['door']:
			self.doors.add_object( xtile, ytile, close_tile_id, openned_id=open_tile_id, state=state ) # Extra params must be KWarg


class GameApp( OledBoot ):
	def __init__( self ):
		super().__init__()
		self.fbtls = FBUtil( self ) # Utility methods on the target FrameBuffer
		self.level_name = None
		self.current_screen = SCREEN_GAMEBOARD
		self.reader = None # Image reader
		self.level  = None # Level information
		self.player = None # Player position, life, inventory, etc

		# Button A & B 
		self.a_pressed_event = EventTimeout()
		self.a_pressed_event.set( False, 10 ) # Initialize it
		self.b_pressed_event = EventTimeout()
		self.b_pressed_event.set( False, 10 ) # Initialize it

		# Gameboard variables
		self.sw_tile = -1 # Screen width in Tile unit
		self.sh_tile = -1
		self.topleft_tile = Coord() # Screen Top Left in Tile unit
		self.player_rel_pos = Coord() # Player relative position (in tile)

		# Player Cursor 
		self.cursor_blink_event = EventTimeout()
		self.cursor_blink_event.set( True, CURSOR_BLINK_MS ) # will expire is 500 ms
		self.error_event = EventTimeout()
		self.error_event.set( True, 1 ) # Don't care about state. Made it expiring immediately
		
		self.chrono_timer = EventTimeout()
		self.chrono_timer.set( 0, 1 ) # Don't care about state. Made it expiring immediately
		self.message_event = EventTimeout()
		self.message_event.set( "", 1 )  # State contains the message. Made it expiring immediately
		self.health_event = EventTimeout()
		self.health_event.set( 0, 1 )  # Don't care about state. Made it expiring immediately

	def a_pressed( self, pin ):
		if (self.a_pressed_event.state==False) and self.a_pressed_event.expired:
			self.a_pressed_event.set( True, BUTTON_MS )		

	def b_pressed( self, pin ):
		if (self.b_pressed_event.state==False) and self.b_pressed_event.expired:
			self.b_pressed_event.set( True, BUTTON_MS )		

	def load_level( self, level_name ):
		self.level_name = level_name
		self.current_screen = SCREEN_GAMEBOARD
		self.reader = open_image( '%s.pbm' % self.level_name )
		self.level  = LevelInfo( self.level_name )
		self.sw_tile = self.width//self.level.tile_width # Screen width in Tile unit
		self.sh_tile = self.height//self.level.tile_height

		self.tileset = self.level.tileset # Kept a local reference to the tileset
		self.player = Player( self.level.tile_width, self.level.tile_height ) 


	def gameboard_display( self ):
		# calculate screen top-left tile (from current player position in the map)
		# considering that player is in the center of screen
		if (self.player.pos.x > self.sw_tile//2) and (self.player.pos.x<self.level.width-(self.sw_tile//2)):
			self.topleft_tile.x = self.player.pos.x - self.sw_tile//2 
		elif self.player.pos.x >= self.level.width-(self.sw_tile//2):
			self.topleft_tile.x = self.level.width - self.sw_tile 
		else:
			self.topleft_tile.x = 0 # Negatif Clipping is not possible SO adjust player pos accordingly!


		if (self.player.pos.y > self.sh_tile//2) and (self.player.pos.y<self.level.height-(self.sh_tile//2)):
			self.topleft_tile.y = self.player.pos.y - self.sh_tile//2
		elif self.player.pos.y >= self.level.height-(self.sh_tile//2):
			self.topleft_tile.y = self.level.height - self.sh_tile
		else:
			self.topleft_tile.y = 0

		# Clip level image in Pixel coordintate
		self.reader.clip( 0+self.topleft_tile.x*self.level.tile_width, 0+self.topleft_tile.y*self.level.tile_height, self.width, self.height )
		# Copy the clipped aread TO a target FrameBuffer (lcd) at is starting
		# position 0,0 for the given clipping width,height .
		self.reader.copy_fast_to(self, 0,0 )

		# Player relative position (in Tile unit)
		self.player_rel_pos.x = self.player.pos.x - self.topleft_tile.x
		self.player_rel_pos.y = self.player.pos.y - self.topleft_tile.y
		
		# Grab objects in the display area
		objs = self.level.objects.in_area( self.topleft_tile.x, self.topleft_tile.y, self.sw_tile, self.sh_tile )
		for obj in objs:
			self.blit( obj.tile, (obj.x_tile-self.topleft_tile.x)*self.level.tile_width, (obj.y_tile-self.topleft_tile.y)*self.level.tile_height ) # A tile is a FrameBuffer
		objs = self.level.actions.in_area( self.topleft_tile.x, self.topleft_tile.y, self.sw_tile, self.sh_tile )
		for obj in objs:
			self.blit( obj.tile, (obj.x_tile-self.topleft_tile.x)*self.level.tile_width, (obj.y_tile-self.topleft_tile.y)*self.level.tile_height ) # A tile is a FrameBuffer
		objs = self.level.poeples.in_area( self.topleft_tile.x, self.topleft_tile.y, self.sw_tile, self.sh_tile )
		for obj in objs:
			self.blit( obj.tile, (obj.x_tile-self.topleft_tile.x)*self.level.tile_width, (obj.y_tile-self.topleft_tile.y)*self.level.tile_height ) # A tile is a FrameBuffer
		objs = self.level.doors.in_area( self.topleft_tile.x, self.topleft_tile.y, self.sw_tile, self.sh_tile )
		for obj in objs:
			self.blit( obj.door_tile, (obj.x_tile-self.topleft_tile.x)*self.level.tile_width, (obj.y_tile-self.topleft_tile.y)*self.level.tile_height ) # A tile is a FrameBuffer

		# Message Popup
		if not self.message_event.expired:
			# print( "Message_event:", self.message_event.state)
			self.fill_rect( 0,0,self.width, 9, 0)
			self.text( self.message_event.state, 0,0, 1 )

		# Cursor Handling
		if self.cursor_blink_event.expired:
			self.cursor_blink_event.set( not(self.cursor_blink_event.state), CURSOR_BLINK_MS )

		if self.cursor_blink_event.state:
			self.blit( self.tileset[PLAYER_TILE_ID], self.player_rel_pos.x*self.level.tile_width, self.player_rel_pos.y*self.level.tile_height )
		elif not(self.chrono_timer.expired):
			self.text( "%2s"%(self.chrono_timer.remain//1000), self.player_rel_pos.x*self.level.tile_width, self.player_rel_pos.y*self.level.tile_height+4, 0 )
		elif not(self.error_event.expired):
			# Blit Error Symbol on FALSE state
			self.blit( self.tileset[ERROR_TILE_ID], self.player_rel_pos.x*self.level.tile_width, self.player_rel_pos.y*self.level.tile_height )

	def gameboard_dir( self, _dir ):
		def can_move_to( x, y ):
			# if not a wall at x,y
			if not self.level.wall.pixel( x, y ):
				# Is the wall also a door ?
				return True
			# Not a door ?	
			_door = self.level.doors.get_object(x,y)
			if _door==None:
				return False
			# Is the door open ?
			if _door.state or not(self.chrono_timer.expired):
				return True
			# Can we open this door?
			if self.player.inventory.count_of(KEY_TILE_ID)>0:
				self.player.inventory.remove_object(KEY_TILE_ID)
				_door.state = 1 # Door openned
				return True 
			return False

		def teleport_from( x, y ):
			# Go from on teleport to another
			# Collect all teleports
			_destin = []
			for _obj in [obj for obj in self.level.actions if obj.tile_id in (TELEPORT_1_TILE_ID,TELEPORT_2_TILE_ID) and obj.x_tile!=x and obj.y_tile!=y ]:
				_destin.append( _obj )
			_target = _destin[random.randint(0,len(_destin)-1)]
			# Find a correct destination for user around the destination
			for xx in range(2):# 0..3
				for yy in range(4):
					if xx==1 and yy==1:
						continue
					if not( 0<= _target.x_tile-1+xx <=99 ) or not( 0<= _target.y_tile-1+yy <=99 ):
						continue
					if self.level.wall.pixel(_target.x_tile-1+xx, _target.y_tile-1+yy):
						continue
					if self.level.actions.get_object(_target.x_tile-1+xx,_target.y_tile-1+yy)!=None:
						continue
					if self.level.objects.get_object(_target.x_tile-1+xx,_target.y_tile-1+yy)!=None:
						continue
					if self.level.poeples.get_object(_target.x_tile-1+xx,_target.y_tile-1+yy)!=None:
						continue
					# Great, we found a place
					self.player.pos.x = _target.x_tile-1+xx
					self.player.pos.y = _target.y_tile-1+yy
					return


		# === RIGHT move =====================================
		if _dir==RIGHT:
			_value = self.player.pos.x + 1
			if _value >= self.level.width:
				_value = self.level.width-1
			if can_move_to(_value, self.player.pos.y ):  # Are we hurting a wall ?
				self.player.pos.x = _value # Accept the move
			else:
				self.error_event.set( True, ERROR_MS )

		# === LEFT  move =====================================
		elif _dir==LEFT:
			_value = self.player.pos.x - 1
			if _value < 0:
				_value = 0
			if can_move_to( _value, self.player.pos.y ):  # Are we hurting a wall ?				
				self.player.pos.x = _value # Accept the move
			else:
				self.error_event.set( True, ERROR_MS )

		# === UP    move =====================================
		elif _dir==UP:
			_value = self.player.pos.y - 1
			if _value < 0:
				_value = 0
			if can_move_to( self.player.pos.x, _value ):  # Are we hurting a wall ?
				self.player.pos.y = _value # Accept the move
			else:
				self.error_event.set( True, ERROR_MS )

		# === DOWN  move =====================================
		elif _dir==DOWN:					
			_value = self.player.pos.y + 1
			if _value >= self.level.height:
				_value = self.level.height-1
			if can_move_to( self.player.pos.x, _value ):  # Are we hurting a wall ?
				self.player.pos.y = _value # Accept the move
			else:
				self.error_event.set( True, ERROR_MS )

		# === Object detection ===============================
		_obj = self.level.objects.get_object( self.player.pos.x, self.player.pos.y )
		if _obj!=None and _obj.visible:
			self.player.inventory.add_object( _obj.tile_id )
			_obj.visible = False

		# === Action detection ===============================
		_obj = self.level.actions.get_object( self.player.pos.x, self.player.pos.y )
		if _obj!=None and _obj.visible:
			if _obj.tile_id==CHRONO_TILE_ID:
				self.message_event.set( "Free-key openner", MESSAGE_MS )
				self.chrono_timer.set( 0, CHRONO_TIME_MS )
				# Object Disapears
				_obj.visible = False
			elif _obj.tile_id in (TELEPORT_1_TILE_ID,TELEPORT_2_TILE_ID):
				self.message_event.set( "Random teleport", MESSAGE_MS )
				teleport_from( self.player.pos.x, self.player.pos.y )
			elif _obj.tile_id == FIRST_AID_TILE_ID:
				self.player.health = 100
				self.message_event.set( "Health %s" % self.player.health, MESSAGE_MS )				
				_obj.visible = False
		
		# === Ennemi detection ===============================
		_obj = self.level.poeples.get_object( self.player.pos.x, self.player.pos.y )
		if _obj!=None and _obj.visible:
			if self.health_event.expired:
				self.health_event.set( 0, HEALTH_IMMUNE_MS )
				self.player.health -= 10
				if self.player.health <= 0:
					self.fill(0)
					self.text("Game Over!",0,25,1)
					self.text("Please reset...",0,56,1)
					self.show()
					exit()
				else:
					self.message_event.set( "Health %s" % self.player.health, MESSAGE_MS )


	def map_display( self ):
		# self.blit( self.level.wall, 10, 0 )
		# Display WALL map (4x4 pixel for space or wall)
		self.fill( 0 )
		# User position os mpcated at center of screen
		x_tile_from = self.player.pos.x - (self.width//2)//4
		y_tile_from = self.player.pos.y - (self.height//2)//4 
		if x_tile_from < 0: 
			x_tile_from = 0
		if y_tile_from < 0:
			y_tile_from = 0
		# Range to copy
		x_range = 128//4
		y_range = 64//4
		if (x_tile_from+x_range)>=self.level.width:
			x_range=self.level.width-x_tile_from
		if y_tile_from+y_range>=self.level.height:
			y_range=self.level.width-y_tile_from
		# Let's copy the screen
		for y in range( y_tile_from, y_tile_from+y_range):
			for x in range( x_tile_from, x_tile_from+x_range):
				_d = self.level.doors.get_object(x,y)
				if _d != None:
					# Draw a door Open else Closed
					if _d.state:
						self.rect( (x-x_tile_from)*4+1,(y-y_tile_from)*4+1, 2,2, 1) 
					else:
						self.line( (x-x_tile_from)*4,(y-y_tile_from)*4, (x-x_tile_from)*4+4,(y-y_tile_from)*4+4, 1)
						self.hline( (x-x_tile_from)*4,(y-y_tile_from)*4+4, 4, 1) 
						self.vline( (x-x_tile_from)*4,(y-y_tile_from)*4, 4, 1)
				else:
					# Draw a wall
					if self.level.wall.pixel(x,y):
						self.rect( (x-x_tile_from)*4,(y-y_tile_from)*4, 4,4, 1)
		# Calculate the cursor position
		x_rel = self.player.pos.x-x_tile_from
		y_rel = self.player.pos.y-y_tile_from
		# Draw cursor position as a blinking Dot 
		if self.cursor_blink_event.state:
			self.fill_rect( x_rel*4, y_rel*4, 4, 4, 1 )
		if self.cursor_blink_event.expired:
			self.cursor_blink_event.set( not(self.cursor_blink_event.state), CURSOR_BLINK_MS )


	def map_dir( self, _dir ):
		pass


	def inventory_display( self ):
		# self.blit( self.level.wall, 10, 0 )
		# Display WALL map (4x4 pixel for space or wall)
		assert len( self.player.inventory )<=9 , "Inventory limited to 9 entry"
		self.fill( 0 )
		self.fill_rect(0,0,self.width,10,1)
		self.text( "Health: %i%%"%self.player.health,8,1,0 )
		print( "inventory", self.player.inventory )
		for y_idx, key_group in enumerate( slice_by( list(self.player.inventory.keys()), 3 )): # Inventory is a tile_id key
			print( "key_groups", key_group )
			for x_idx, key_tile_id in enumerate( key_group ):
				print( "key_tile_id", key_tile_id, type(key_tile_id) )
				yy = 11+17*y_idx
				xx = (42+1)*x_idx
				print( "inventory", self.player.inventory )
				_count = self.player.inventory[key_tile_id]				
				self.blit( self.level.tileset[key_tile_id], xx, yy )
				self.text( str(_count), xx+16+3, yy+4, 1 )


	def inventory_dir( self, _dir ):
		pass


	def run( self ):
		# Attach Button IRQ 
		self.a.irq( handler=self.a_pressed, trigger=Pin.IRQ_RISING )
		self.b.irq( handler=self.b_pressed, trigger=Pin.IRQ_RISING )

		# Identify starting position
		self.player.pos.set( self.level.initial_player_pos ) # Set initial position (in tile)
		
		cursor_move_event = EventTimeout()
		cursor_move_event.set( 0, CURSOR_MOVE_MS )

		while True:
			start = time.ticks_ms()
			if self.current_screen==SCREEN_GAMEBOARD:
				self.gameboard_display()
			elif self.current_screen==SCREEN_MAP:
				self.map_display()
			elif self.current_screen==SCREEN_INVENTORY:
				self.inventory_display()

			# refresh screen
			self.show()


			# Capture the direction (priority to buttons)
			if self.a_pressed_event.state and self.a_pressed_event.expired:
				self.a_pressed_event.set( False, BUTTON_MS )
				_dir = BTN_A
				if self.current_screen==SCREEN_GAMEBOARD:
					self.current_screen = SCREEN_MAP
				else:
					self.current_screen = SCREEN_GAMEBOARD

			elif self.b_pressed_event.state and self.b_pressed_event.expired:
				self.b_pressed_event.set( False, BUTTON_MS )
				_dir = BTN_B
				if self.current_screen==SCREEN_GAMEBOARD:
					self.current_screen = SCREEN_INVENTORY
				else:
					self.current_screen = SCREEN_GAMEBOARD

			else:
				# Get joystick direction
				_dir = self.dir


			# Transfert direction to appropriate routine
			if self.current_screen==SCREEN_GAMEBOARD:
				if cursor_move_event.expired:
					self.gameboard_dir( _dir )
					cursor_move_event.set( _dir, CURSOR_MOVE_MS)
			elif self.current_screen==SCREEN_MAP:
				self.map_dir( _dir )
			elif self.current_screen==SCREEN_INVENTORY:
				self.inventory_dir( _dir )

			print( 'frame', time.ticks_diff( time.ticks_ms(), start), self.player.pos )



game = GameApp()
game.load_level( 'level1' )
game.run()
