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

from java.lang            import Exception, IllegalArgumentException
from com.ibm.ws.scripting import ScriptingException
from net.sf.wspydmin      import AdminConfig

########################################################################
##                         WebSphere types                            ##
########################################################################

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
	def __init__(self, elemType):
		if not hasattr(elemType, 'typename'):
			raise IllegalArgumentException, 'Invalid element type received'
		
		elemTypename = elemType.typename
		if (elemTypename is None) or (len(elemTypename) == 0):
			raise IllegalArgumentException, 'Invalid element type received'
		
		WasDataType.__init__(self, elemType.typename + '*')
		self.elemType = elemType
	
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
			obj.append(self.elemType.from_str(elem))
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
				str = str + self.elemType.to_str(elem)
				count = count + 1
		else:
			str = str + self.elemType.to_str(value)
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
	
	def __init__(self, typename, klass):
		WasDataType.__init__(self, typename)
		self.klass = klass
	
	def from_str(self, value):
		if (value == '') or (value is None): return None
		return self.klass(value)
	
	def to_str(self, value):
		if value is None: return ''
		return self.klass.__getconfigid__(value)

########################################################################
##                      WebSphere metaclasses                         ##
########################################################################

WAS_METADATA_EMPTY = {
	'DEF_ID'    : None,
	'DEF_ATTRS' : {},
	'DEF_SCOPE' : None,
	'DEF_MTHDS' : [],
	'DEF_TPL'   : None,
	'DEF_PROPS' : {},
}

class WasObjectMethodWrapper:

	def __init__(self, func, inst):
		self.func = func
		self.inst = inst
		self.__name__ = self.func.__name__

	def __call__(self, *args, **kw):
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

class WasObjectHelper:
	
	__methodwrapper__ = WasObjectMethodWrapper
	
	def __helperinit__(self, klass):
		self.__klass__ = klass
		self.__type__  = klass.__name__
		self.__super__ = WasObjectSuperHelper(self, klass)
	
	def __getattr__(self, name):
		# Invoked for any attr not in the instance's __dict__
		try:
			raw = self.__klass__.__getattr__(name)
		except AttributeError:
			try:
				ga = self.__klass__.__getattr__('__usergetattr__')
			except (KeyError, AttributeError):
				return self.__missedattr__(name)
			return ga(self, name)
		
		if type(raw) != types.FunctionType:
			return raw
		return self.__methodwrapper__(raw, self)
	
	def __missedattr__(self, name):
		raise AttributeError, name

class WasObjectClass:
	__helper__    = WasObjectHelper
	__inited      = 0
	
	__OBJ_TYPES__ = {}

	def __init__(self, name, bases = (), dict = {}):
		try:
			ge = dict['__getattr__']
		except KeyError:
			pass
		else:
			dict['__usergetattr__'] = ga
			del dict['__getattr__']
		
		self.__name__     = name
		self.__bases__    = bases
		self.__realdict__ = dict
		
		if not WasObjectClass.__OBJ_TYPES__.has_key(name):
			WasObjectClass.__OBJ_TYPES__[name] = self
		
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
			return self.__missedattr__(name)
	
	def __setattr__(self, name, value):
		if not self.__inited:
			self.__dict__[name] = value
		else:
			self.__realdict__[name] = value
	
	def __call__(self, *args, **kwargs):
		inst = self.__helper__()
		inst.__helperinit__(self)
		
		try:
			init = getattr(inst, '__init__')
			apply(init, args, kw)
		except AttributeError:
			pass
		
		try:
			post = getattr(inst, '__postinit__')
			apply(post, (inst,), {})
		except AttributeError:
			pass
		
		return inst

##
# Base WAS object class which should be used as the
# primary super class for any WAS instance
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

########################################################################
##                      Utility functions                             ##
########################################################################

##
# Data type map used internally for resolving WebSphere types
__WAS_DATATYPES__ = {
	WasBooleanDataType.TYPENAME : WasBooleanDataType(),
	WasIntegerDataType.TYPENAME : WasIntegerDataType(),
	WasStringDataType.TYPENAME  : WasStringDataType()
}

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
	elif __WAS_DATATYPES__.has_key(typename):
		return __WAS_DATATYPES__[typename]
	else:
		if not WasObjectClass.__OBJ_TYPES__.has_key(typename):
			raise IllegalArgumentException, "Unknown type name: '%s'" % typename
		return WasObjectDataType(typename, WasObjectClass.__OBJ_TYPES__[typename])
