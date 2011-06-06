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

import types, logging
import AdminTask, AdminConfig, AdminControl, AdminApp, Help

from java.lang         import Class as JavaClass, Exception as JavaException, IllegalArgumentException, ClassNotFoundException
from java.lang.reflect import Array as JavaArray

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
		for elem in value.split(' ,'):
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
				count += 1
		else:
			str = str + self.element_type.to_str(value)
		str = str + ']'
		return str

class WasEnumDataType(WasDataType):
	TYPENAME = 'ENUM'
	
	def __init__(self, values):
		WasDataType.__init__(self, WasEnumDataType.TYPENAME)
		self.values = values
		for value in values:
			self.__dict__[value] = value
	
	def from_str(self, value):
		if self.__dict__.has_key(value):
			return self.__dict__[value]
		else:
			raise "Invalid enum value: %s" % value
	
	def to_str(self, value):
		if self.__dict__.has_key(str(value)):
			return self.__dict__[str(value)]
		else:
			raise "Invalid enum value: %s" % value

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

def was_define_type(typename, typeclass):
	if __WAS_DATATYPES.has_key(typename):
		raise WasDataTypeError, 'Type already registered: %s' % typename
	__WAS_DATATYPES[typename] = typeclass()

def was_define_class(klass, typename = None):
	if (typename is None):
		typename = klass.__name__
	if __WAS_OBJTYPES.has_key(typename):
		raise WasDataTypeError, 'Object class already registered: %s' % typename
	__WAS_OBJTYPES[typename] = klass
	logging.debug("Defined class '%s' with bases: %s.", typename, klass.__bases__)
	
# Define WebSphere's configuration primitive types
was_define_type(WasBooleanDataType.TYPENAME, WasBooleanDataType)
was_define_type(WasIntegerDataType.TYPENAME, WasIntegerDataType)
was_define_type(WasStringDataType.TYPENAME, WasStringDataType)

########################################################################
##                      Utility functions                             ##
########################################################################

def was_type(typename):
	if (typename == '') or (typename is None): return None
	if typename.endswith('*'):
		typename = typename[0:-1]
		return WasArrayDataType(was_type(typename))
	elif typename.startswith('ENUM'):
		values = typename.split('(')[1].split(', ')
		return WasEnumDataType(values)
	elif __WAS_DATATYPES.has_key(typename):
		return __WAS_DATATYPES[typename]
	else:
		if not __WAS_OBJTYPES.has_key(typename):
			raise WasDataTypeError, typename
		return WasObjectDataType(__WAS_OBJTYPES[typename])

def java_type(typename):
	if (typename == '') or (typename is None): return None
	try:
		return JavaClass.forName(typename)
	except ClassNotFoundException:
		pass
	if typename.startswith('[L'):
		elementType = java_type(typename[2:-1])
		return JavaArray.new(elementType, 0).getClass()
	return None

########################################################################
##                      WebSphere metaclasses                         ##
########################################################################

class WasObjectMethodWrapper:

	def __init__(self, func, inst):
		self.func     = func
		self.inst     = inst
		self.__name__ = self.func.__name__

	def __call__(self, *args, **kw):
		logging.debug("Invoking function '%s.%s' with args: %s", self.inst.__wasclass__.__name__, self.__name__, args)
		return apply(self.func, (self.inst,) + args, kw)

class WasObjectSuperHelper:
	
	def __init__(self, instance, klass):
		self.instance = instance
		self.klass = klass
	
	def __getattr__(self, name):
		for base in self.klass.__bases__:
			try:
				return base.__getattr__(name)
			except AttributeError:
				pass
		raise AttributeError, name
		
	def __call__(self, *args, **kwargs):
		for base in self.klass.__bases__:
			try:
				init = getattr(base, '__init__')
				apply(init, (self.instance,) + args, kwargs)
			except AttributeError:
				pass

class WasObjectClassHelper:
	
	__methodwrapper__ = WasObjectMethodWrapper
	
	def __helperinit__(self, klass):
		self.__wasclass__ = klass
		self.__wassuper__ = WasObjectSuperHelper(self, klass)
	
	def __getattr__(self, name):
		# Invoked for any attr not in the instance's __dict__
		try:
			raw = self.__wasclass__.__getattr__(name)
		except AttributeError:
			try:
				ga = self.__wasclass__.__getattr__('__usergetattr__')
			except (KeyError, AttributeError):
				return self.__missedattr__(name)
			else:
				return ga(self, name)
		else:
			if type(raw) != types.FunctionType:
				return raw
			return self.__methodwrapper__(raw, self)
	
	def __define_classtype__(self):
		was_define_class(self.__wasclass__)
	
	def __define_instance__(self):
		pass
	
	def __missedattr__(self, name):
		raise AttributeError, name

class WasObjectClass:
	__helper__    = WasObjectClassHelper
	__inited      = 0

	def __init__(self, name, bases = (), dict = {}):
		try:
			ga = dict['__getattr__']
		except KeyError:
			pass
		else:
			dict['__usergetattr__'] = ga
			del dict['__getattr__']
		
		self.__name__     = name
		self.__bases__    = bases
		self.__realdict__ = dict
		
		was_define_class(self)
		self.__inited = 1
	
	def __getattr__(self, name):
		try:
			return self.__realdict__[name]
		except KeyError:
			for base in self.__bases__:
				try:
					return base.__getattr__(name)
				except AttributeError:
					pass
			raise AttributeError, name
	
	def __setattr__(self, name, value):
		if not self.__inited:
			self.__dict__[name] = value
		else:
			self.__realdict__[name] = value
	
	def __call__(self, *args, **kwargs):
		inst = self.__helper__()
		inst.__helperinit__(self)
		#inst.__define_classtype__()
		logging.debug("Creating new instance of class '%s'", self.__name__)
		
		try:
			init = getattr(inst, '__init__')
			apply(init, args, kwargs)
		except AttributeError:
			pass
		
		inst.__define_instance__()
		return inst

##
# Base WAS object class which should be used as the
# primary super class for any WAS object instance
WasObject = WasObjectClass('WasObject')

class ChainedMethodInvoker:
	def __init__(self, metaclass, methodname, instances):
		self.metaclass   = metaclass
		self.methodname  = methodname
		self.instances   = instances
	
	def __call__(self, *args, **kwargs):
		retval = None
		for inst in self.instances:
			retval = apply(self.methodname, (inst,) + args, kwargs)
		return retval