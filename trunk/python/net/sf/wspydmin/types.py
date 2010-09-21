# WSPydmin - WebSphere Python Administration Library
# Copyright (C) 2010  Antonio Alonso Domínguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import copy, types

from java.lang import IllegalArgumentException

########################################################################
##                         WebSphere types                            ##
########################################################################

class WasDataTypeError(Exception):
	pass

##
# Abstract representation of a WebSphere type.
# A WebSphere type is any primitive or object supported by
# the WebSphere Application Server
#
# @author: A. Alonso Dominguez
class WasDataType:
	
	##
	# Initializes the type
	# @param typename: name of this type 
	def __init__(self, typename):
		if (typename is None) or (typename == ''):
			raise IllegalArgumentException, "A typename must be specified"
		self.typename = typename
	
	##
	# Transforms a string into a python valid value
	# @param value: a string value
	# @return: nothing
	def from_str(self, value):
		pass
	
	##
	# Transforms any value into a string
	# @param value: any value
	# @return: nothing
	def to_str(self, value):
		pass
	
	##
	# Offers a string representation of this type
	def __str__(self):
		return self.typename

##
# Typed array implementation
#
# @author: A. Alonso Dominguez
class WasArrayDataType(WasDataType):
	
	##
	# Initializes the array type
	# @param elemType: WasDataType for the elements of this array type
	def __init__(self, element_type):
		if element_type is None:
			raise IllegalArgumentException, "element type can't be null"
		if not hasattr(element_type, 'typename'):
			raise IllegalArgumentException, 'Invalid element type received'
		
		element_typename = element_type.typename
		if (element_typename is None) or (len(element_typename) == 0):
			raise IllegalArgumentException, 'Invalid element type received'
		
		WasDataType.__init__(self, element_typename + '*')
		self.element_type = element_type
	
	##
	# Transforms a string into an array of values
	# @param value: any string
	# @return: a python list containing the elements listed in the string
	def from_str(self, value):
		if (value == '') or (value is None): return None
		obj = []
		if value.startswith('[') and value.endswith(']'):
			value = value[1:len(value)-1]
		values = value.split(' ,')
		for elem in values:
			obj.append(self.element_type.from_str(elem))
		return obj

	##
	# Transforms a python list into a string which represents the array data
	# @param value: a python list
	# @return: a string representing the array data	
	def to_str(self, value):
		if value is None: return ''
		str = '['
		if type([]) == type(value):
			count = 0
			for elem in value:
				if count > 0: str = str + ','
				str = str + self.element_type.to_str(elem)
				count = count + 1
		else:
			str = str + self.element_type.to_str(value)
		str = str + ']'
		return str

##
# Boolean data types handler
#
# @author: A. Alonso Dominguez
class WasBooleanDataType(WasDataType):
	TYPENAME = 'boolean'

	##
	# Initializes the boolean data type
	def __init__(self):
		WasDataType.__init__(self, WasBooleanDataType.TYPENAME)
	
	##
	# Transforms any string received into a python boolean (int)
	# @param value: any string
	# @return: a python boolean (int)
	def from_str(self, value):
		if (value == '') or (value is None): return 0
		return ((value == 'true') or (value == 'True') or (value == 'TRUE') or (value == '1'))
	
	##
	# Transforms a python boolean (a int) into a boolean string
	# @param value: a python boolean
	def to_str(self, value):
		if value: return 'true'
		else:     return 'false'

##
#
# @author: A. Alonso Dominguez
class WasIntegerDataType(WasDataType):
	TYPENAME = 'Integer'
	
	def __init__(self):
		WasDataType.__init__(self, WasIntegerDataType.TYPENAME)
	
	def from_str(self, value):
		if (value == '') or (value is None): 
			return None
		return int(value)
	
	def to_str(self, value):
		if value is None: return ''
		return '%i' % value

##
#
# @author: A. Alonso Dominguez
class WasStringDataType(WasDataType):
	TYPENAME = 'String'
	
	def __init__(self):
		WasDataType.__init__(self, WasStringDataType.TYPENAME)
	
	def from_str(self, value):
		if (value == '') or (value is None): return None
		if value.startswith('"') and value.endswith('"'):
			value = value[1:-1]
		return value
	
	def to_str(self, value):
		if value is None: return ''
		return '"' + str(value) + '"'

##
#
# @author: A. Alonso Dominguez
class WasObjectDataType(WasDataType):
	
	def __init__(self, klass):
		WasDataType.__init__(self, klass.__name__)
		self.klass = klass
	
	def from_str(self, value):
		if (value == '') or (value is None): return None
		return self.klass(value)
	
	def to_str(self, value):
		if value is None: return ''
		return self.klass.__getconfigid__(value)


##
# Data type map used internally for resolving WebSphere types
__WAS_DATATYPES = {
	WasBooleanDataType.TYPENAME : WasBooleanDataType(),
	WasIntegerDataType.TYPENAME : WasIntegerDataType(),
	WasStringDataType.TYPENAME  : WasStringDataType()
}

__WAS_OBJECT_CLASSES = {
}

def was_define_type(typename, typeclass):
	if __WAS_DATATYPES.has_key(typename):
		raise WasDataTypeError, 'Type already registered: %s' % typename
	__WAS_DATATYPES[typename] = typeclass

def was_define_class(klass):
	if __WAS_OBJECT_CLASSES.has_key(klass.__name__):
		raise WasDataTypeError, 'Object class already registered: %s' % klass.__name__
	__WAS_OBJECT_CLASSES[klass.__name__] = klass

def was_type(typename):
	if (typename == '') or (typename is None): return None
	if typename.endswith('*'):
		typename = typename[0:-1]
		return WasArrayDataType(was_type(typename))
	elif __WAS_DATATYPES.has_key(typename):
		return __WAS_DATATYPES[typename]
	else:
		if not __WAS_OBJECT_CLASSES.has_key(typename):
			raise IllegalArgumentException, "Unknown type name: '%s'" % typename
		return WasObjectDataType(typename, __WAS_OBJECT_CLASSES[typename])
