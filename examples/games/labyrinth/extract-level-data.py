#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Extract the data from Tiled tmx file for the labyrinth MicroPython game for Pico-Oled-Boot .
   This utility is designed for 16x16px tileset.

   * tmx-file must contains the layers: map, object, action, poeple (created by Tiled software).
   * wall-ids-file : comma separated file with Tile_ID of walls (maintain by user).

Will create several data files with <basename> filenames

Usage:
  extract-level-data.py <tmx-file> <basename> <wall-ids-file> <door-ids-file>

Examle:
  python3 extract-level-data.py tiled-project/level1.tmx level1 tiled-project/wall.ids tiled-project/door.ids
"""

from docopt import docopt
from pyframebuf import FrameBuffer
import xml.etree.ElementTree as et
import base64, struct, json

def attr_value( node, attr_name, cast_as = None ):
	# print( node, node.attrib )
	if not( attr_name in node.attrib ):
		raise ValueError( "No attribute %s in %s node" % (attr_name, node.tag) )
	val = node.attrib[attr_name]
	if cast_as != None:
		return cast_as(val)
	return val

class id_list( list ):
	def __init__( self, filename ):
		super().__init__()
		with open( filename ) as f:
			lines = f.readlines()
			for line in lines:
				line = line.replace('\r','').replace('\n','').replace(' ','')
				if len(line)==0:
					continue
				if line[0]=='#': # comment
					continue
				for item in line.split(','):
					self.append( int(item) )

class door_item:
	__slot__ = ('closed_id','openned_id')
	def __init__( self, id ):
		self.closed_id = id // 10000
		self.openned_id = id % 10000

	def __repr__( self ):
		return "<%s closed=%i, openned=%i>" % (self.__class__.__name__, self.closed_id, self.openned_id)


class door_list( id_list ):
	def __init__( self, filename ):
		super().__init__( filename )
		for i in range(len(self)):
			self[i] =  door_item( self[i] ) # 

	def which_door( self, tile_id ):
		# check if the tile is one of the doors.
		# return the corresponding door_item object (or None)
		for item in self:
			if (item.closed_id==tile_id) or (item.openned_id==tile_id):
				return item
		return None

class App:
	def __init__( self, tmx_filename, basename, wall_ids_filename, door_ids_filename ):
		self.tree = et.parse( tmx_filename )
		self.root = self.tree.getroot()
		self.basename = basename 
		# identify the tileset firstgid
		self.firstgid = attr_value( self.find_node(self.root,'tileset'), 'firstgid', cast_as=int )
		# Various Layout
		self.map_node = self.find_layer( 'map' )
		self.object_node = self.find_layer( 'object' )
		self.action_node = self.find_layer( 'action' )
		self.poeple_node = self.find_layer( 'poeple' )
		# Map size
		self.height = attr_value( self.map_node, 'height', cast_as=int )
		self.width  = attr_value( self.map_node, 'width', cast_as=int )
		self.tilewidth = attr_value( self.root, 'tilewidth', cast_as=int )
		self.tileheight = attr_value( self.root, 'tileheight', cast_as=int )
		# Loading data
		self.wall_ids = id_list( wall_ids_filename )
		self.door_ids = door_list( door_ids_filename ) # list of 00860066 <ClosedTileID><OpennedTileID>
		print( self.door_ids )

	def find_node( self, node, tag_name ):
		for child in node:
			if (child.tag == tag_name ):
				return child
		raise ValueError( 'No node %s under %s' % (tag_name, node) )

	def extract_data( self, parent_node ):
		# Extract data enclosed in the <data> subnode
		# chunks of 4 bytes (little-endian unsigned 32-bit integers) to retrieve the exact Tile ID and its corresponding flipping flags.
		data_node = self.find_node( parent_node, 'data' )
		if attr_value( data_node, 'encoding')!='base64':
			raise ValueError( "base64 encoding expected for %s data node" % parent_node )
		if "compression" in data_node.attrib:
			raise ValueError( "compression not supported for data node %s" % parent_node )
		_bytes = base64.b64decode( data_node.text )
		# Clean ID = value & 0x1FFFFFFF 
		#   Filter bit 32 = vertical flip
		#          bit 31 = horizontal flip
		#          bit 30 = anti-diagonal flip (90° rotate)
		# Local ID = Clean ID - firstgid 
		return list( [ (vals[0]&0x1FFFFFFF)-self.firstgid for vals in  struct.iter_unpack( "<I", _bytes)] )

	def find_layer( self, name ):
		for child in self.root:
			if (child.tag == 'layer') and ( child.attrib['name']==name ):
				return child
		raise ValueError( 'No layer named %s' % name )

	def get_layer_size( self, layer_node ):
		# Return a tuple width, high
		return ( attr_value( layer_node, 'width', cast_as=int ), attr_value( layer_node, 'height', cast_as=int ) )


	def layer_offset( self, x, y, map_height=None, map_width=None ):
		# return the byte offset in data map (for the given map size of width & height)
		if map_height==None:
			map_height = self.height
		if map_width==None:
			map_width = self.width
		return y*map_width+x

	def is_wall_tile( self, tile_id ):
		return False

	def run( self ):

		# WALL bit mapping
		#byte_per_row = (self.width//8) + (1 if self.width%8 != 0 else 0)
		_framebuf = FrameBuffer( self.width, self.height )
		_door = [] # List of doors detected in the tile 
		map_data = self.extract_data( self.map_node ) # map is a list of integer
		for y in range( self.height ):			
			for x in range( self.width ):
				tile_id = map_data[ self.layer_offset( x, y ) ]
				# print( x, y, tile_id, tile_id in self.wall_ids )				
				_framebuf.pixel( x, y, tile_id in self.wall_ids )
				# Detect if tile is a door
				door_item = self.door_ids.which_door( tile_id ) # Get the door info or None for that tile
				if door_item!=None:
					_door.append( [x,y,door_item.closed_id,door_item.openned_id, 1 if tile_id==door_item.openned_id else 0 ] ) # x,y, closed_tileID, openned_tileID, state=1 if openned else 0

		filename = '%s.wall' % self.basename
		with open( filename, 'wb' ) as f:
			f.write(_framebuf)
		print( "%s written!" % filename )
		print( '%i door identified!' % len(_door) )

		# Identify the ACTIONS
		# stored as a tuple (x,y,tile_ID)
		action_data = self.extract_data( self.action_node )
		_action = []
		for y in range( self.height ):			
			for x in range( self.width ):
				tile_id = action_data[ self.layer_offset( x, y ) ]
				if tile_id < 0:
					continue
				# print( x, y, tile_id, tile_id in self.wall_ids )				
				_action.append( (x,y,tile_id) )
		print( '%i action identified!' % len(_action) )

		# Identify the OBJECTS
		# stored as a tuple (x,y,tile_ID)
		object_data = self.extract_data( self.object_node )
		_object = []
		for y in range( self.height ):			
			for x in range( self.width ):
				tile_id = object_data[ self.layer_offset( x, y ) ]
				if tile_id < 0:
					continue
				# print( x, y, tile_id, tile_id in self.wall_ids )				
				_object.append( (x,y,tile_id) )
		print( '%i object identified!' % len(_object) )

		# Identify the POEPLES
		# stored as a tuple (x,y,tile_ID)
		poeple_data = self.extract_data( self.poeple_node )
		_poeple = []
		for y in range( self.height ):			
			for x in range( self.width ):
				tile_id = poeple_data[ self.layer_offset( x, y ) ]
				if tile_id < 0:
					continue
				# print( x, y, tile_id, tile_id in self.wall_ids )				
				_poeple.append( (x,y,tile_id) )
		print( '%i poeple identified!' % len(_poeple) )


		# Save configuration information
		filename = '%s.json' % self.basename
		_d = {}
		_d['width']=self.width
		_d['height']=self.height
		_d['tilewidth']=self.tilewidth
		_d['tileheight']=self.tileheight
		_d['poeple']=_poeple
		_d['action']=_action
		_d['object']=_object
		_d['door']=_door
		with open( filename, "w") as f:
			json.dump( _d, f )
		print( "%s written!" % filename )

if __name__ == '__main__':
	arguments = docopt(__doc__, version='extract-level-data.py 1.0')
	# print(arguments)
	app = App( arguments['<tmx-file>'], arguments['<basename>'], arguments['<wall-ids-file>'], arguments['<door-ids-file>'] )
	print( '%s loaded ...' % arguments['<tmx-file>'] )
	print( 'Wall IDs:', app.wall_ids )
	print( 'Door IDs:', app.door_ids )
	print( 'map size is %i x %i tiles' % (app.width,app.height) )
	app.run()
	
