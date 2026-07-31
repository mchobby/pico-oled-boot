#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" FrameBuffer implementation for Python """

class FrameBuffer( bytearray ):
	def __init__( self, w, h ):
		self.width = w
		self.height = h
		self.byte_per_row = (self.width//8) + (1 if self.width%8 != 0 else 0)
		super().__init__( self.byte_per_row*self.height )

	def pixel( self, x, y, value = None ):
		# Identify the byte
		byte_offset = (y*self.byte_per_row)+(x//8)
		bit_offset = 7-(x%8) # Bits in the same order than pixels
		#print( 'bit_offset', byte_offset, bit_offset, value)
		# Set or get the pixel
		if value == None:
			val = self[byte_offset]
			if val & (0b1<<bit_offset):
				return 1
			return 0
		else:
			#print( "y=%i, x=%i => byte %i bit %i" % (y,x,byte_offset,bit_offset) )
			val = self[byte_offset]
			val = val & (0xFF ^ (0b1<<bit_offset)) # Reset target bit
			if value: # set target bit value (if it applies)
				val = val | (0b1<<bit_offset)
			self[byte_offset] = val

