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

# import WAS objects

__author__  = "A. Alonso Dominguez <alonsoft@users.sf.net>"
__status__  = "alpha"
__version__ = "0.2.0"

import AdminTask, AdminConfig, AdminControl, AdminApp, Help
from java.lang             import Class as JavaClass, Array as JavaArray, Exception as JavaException, IllegalArgumentException

########################################################################
##                   WebSphere basic data types                       ##
########################################################################

class WasDataTypeError(Exception):
	pass

class WasDataType:
	"""
	Abstract representation of a WebSphere type.
	A WebSphere type is any primitive or object supported by
	the WebSphere Application Server

	@author: A. Alonso Dominguez
	"""

	def __init__(self, typename):
		"""
		Initializes the type
		@param typename: name of this type 
		"""
		if (typename is None) or (typename == ''):
			raise IllegalArgumentException, "A typename must be specified"
		self.typename = typename

	def from_str(self, value):
		"""
		Transforms a string into a python valid value
		@param value: a string value
		@return: nothing
		"""
		pass

	def to_str(self, value):
		"""
		Transforms any value into a string
		@param value: any value
		@return: nothing
		"""
		pass

	def __str__(self):
		"""
		Offers a string representation of this type
		"""
		return self.typename

class WasArrayDataType(WasDataType):
	"""
	Typed array implementation

	@author: A. Alonso Dominguez
	"""

	def __init__(self, element_type):
		"""
		Initializes the array type
		@param elemType: ResourceDataType for the elements of this array type
		"""
		if element_type is None:
			raise IllegalArgumentException, "element type can't be null"
		if not hasattr(element_type, 'typename'):
			raise IllegalArgumentException, 'Invalid element type received'

		element_typename = element_type.typename
		if (element_typename is None) or (len(element_typename) == 0):
			raise IllegalArgumentException, 'Invalid element type received'

		WasDataType.__init__(self, element_typename + '*')
		self.element_type = element_type

	def from_str(self, value):
		"""
		Transforms a string into an array of values
		@param value: any string
		@return: a python list containing the elements listed in the string
		"""
		if (value == '') or (value is None): return None
		obj = []
		if value.startswith('[') and value.endswith(']'):
			value = value[1:len(value)-1]
		values = value.split(' ,')
		for elem in values:
			obj.append(self.element_type.from_str(elem))
		return obj

	def to_str(self, value):
		"""
		Transforms a python list into a string which represents the array data
		@param value: a python list
		@return: a string representing the array data	
		"""
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

class WasBooleanDataType(WasDataType):
	"""
	Boolean data types handler

	@author: A. Alonso Dominguez
	"""
	TYPENAME = 'boolean'

	def __init__(self):
		"""
		Initializes the boolean data type
		"""
		WasDataType.__init__(self, WasBooleanDataType.TYPENAME)

	def from_str(self, value):
		"""
		Transforms any string received into a python boolean (int)
		@param value: any string
		@return: a python boolean (int)
		"""
		if (value == '') or (value is None): return 0
		return ((value == 'true') or (value == 'True') or (value == 'TRUE') or (value == '1'))

	def to_str(self, value):
		"""
		Transforms a python boolean (a int) into a boolean string
		@param value: a python boolean
		"""
		if type("") == type(value):
			return self.from_str(value)
		elif value: return 'true'
		else:     return 'false'

class WasIntegerDataType(WasDataType):
	"""

	@author: A. Alonso Dominguez
	"""
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

class WasStringDataType(WasDataType):
	"""

	@author: A. Alonso Dominguez
	"""
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

class WasObjectDataType(WasDataType):
	"""

	@author: A. Alonso Dominguez
	"""

	def __init__(self, klass):
		WasDataType.__init__(self, klass.__name__)
		self.klass = klass

	def from_str(self, value):
		if (value == '') or (value is None): return None
		return self.klass(value)

	def to_str(self, value):
		if value is None: return ''
		return self.klass.__getconfigid__(value)

########################################################################
##                   WebSphere Types Registry                         ##
########################################################################

__WAS_DATATYPES = {
}

__WAS_OBJTYPES = {
}

def __was_define_type(typename, typeclass):
	if __WAS_DATATYPES.has_key(typename):
		raise WasDataTypeError, 'Type already registered: %s' % typename
	__WAS_DATATYPES[typename] = typeclass()

def __was_define_class(klass):
	if __WAS_OBJTYPES.has_key(klass.__name__):
		raise WasDataTypeError, 'Object class already registered: %s' % klass.__name__
	__WAS_OBJTYPES[klass.__name__] = klass
	
# Define WebSphere's configuration primitive types
__was_define_type(WasBooleanDataType.TYPENAME, WasBooleanDataType)
__was_define_type(WasIntegerDataType.TYPENAME, WasIntegerDataType)
__was_define_type(WasStringDataType.TYPENAME, WasStringDataType)

########################################################################
##                      Utility functions                             ##
########################################################################

def was_getconfigid(id):
	if id is None: return None
	
	try:
		obj = AdminConfig.getid(id).splitlines()[0]
		if (obj is None) or (obj == ''):
			obj = None
		return obj
	except IndexError:
		pass
	except ScriptingException:
		pass
	return None

def was_type(typename):
	if (typename == '') or (typename is None): return None
	if typename.endswith('*'):
		typename = typename[0:-1]
		return WasArrayDataType(was_type(typename))
	elif __WAS_DATATYPES.has_key(typename):
		return __WAS_DATATYPES[typename]
	else:
		if not __WAS_OBJTYPES.has_key(typename):
			raise IllegalArgumentException, "Unknown type name: '%s'" % typename
		return WasObjectDataType(__WAS_OBJTYPES[typename])

def java_type(typename):
	if (typename == '') or (typename is None): return None
	if typename.startswth('java.'):
		return JavaClass.forName(typename)
	if typename.startswith('[L'):
		elementType = java_type(typename[2:-1])
		return JavaArray.new(elementType, 0).getClass()
	return None

