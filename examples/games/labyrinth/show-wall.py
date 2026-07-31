#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Show the .wall data file info ascii output.
	Will load the json & wall file to display its content

Usage:
  show-wall.py <basename>

Examle:
  python3 show-wall.py level1
"""

from docopt import docopt
from pyframebuf import FrameBuffer
import json


class App:
	def __init__( self, basename ):
		filename = "%s.json" % basename
		print("loading %s ..." % filename )
		with open( filename ) as f:
			_param = json.load( f )
		self.height = _param['height']
		self.width  = _param['width']

		filename = "%s.wall" % basename
		print("loading %s ..." % filename )
		with open( filename, "rb" ) as f:
			self.framebuff = FrameBuffer( self.width, self.height )
			f.readinto( self.framebuff )


	def run( self ):
		# print( self.framebuff )
		for y in range( self.height ):
			line=[]
			for x in range( self.width ):
				line.append( 'X' if self.framebuff.pixel(x,y) else '.' )
			print( ''.join(line))
		

if __name__ == '__main__':
	arguments = docopt(__doc__, version='extract-level-data.py 1.0')
	# print(arguments)
	app = App( arguments['<basename>'] )
	app.run()
