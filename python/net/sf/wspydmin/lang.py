## WSPydmin - WebSphere Python Administration Library
## Copyright (C) 2010  Antonio Alonso Domínguez
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##

import copy, types

from java.lang            import Exception, IllegalArgumentException
from com.ibm.ws.scripting import ScriptingException
from net.sf.wspydmin      import AdminConfig

########################################################################
##                         WebSphere types                            ##
########################################################################

class WasDataType:
	def __init__(self, typename):
		self.typename = typename
	
	def from_str(self, value):
		pass
	
	def to_str(self, value):
		pass
	
	def __str__(self):
		return self.typename

class WasArrayDataType(WasDataType):
	def __init__(self, elemType):
		WasDataType.__init__(self, elemType.typename + '*')
		self.elemType = elemType
	
	def from_str(self, value):
		if (value == '') or (value is None): return None
		obj = []
		if value.startswith('[') and value.endswith(']'):
			value = value[1:len(value)-1]
		values = value.split(' ,')
		for elem in values:
			obj.append(self.elemType.from_str(elem))
		return obj
	
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

class WasBooleanDataType(WasDataType):
	TYPENAME = 'boolean'

	def __init__(self):
		WasDataType.__init__(self, WasBooleanDataType.TYPENAME)
	
	def from_str(self, value):
		if (value == '') or (value is None): return 0
		return (value == 'true') or (value == 'True') or (value == 'TRUE') or (value == '1')
	
	def to_str(self, value):
		if value: return 'true'
		else:     return 'false'

class WasStringDataType(WasDataType):
	TYPENAME = 'String'
	
	def __init__(self):
		WasDataType.__init__(self, WasStringDataType.TYPENAME)
	
	def from_str(self, value):
		if (value == '') or (value is None): return None
		if value.startswith('"') and value.endswith('"'):
			value = value[1:len(value)-1]
		return value
	
	def to_str(self, value):
		if value is None: return ''
		return '"' + str(value) + '"'

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

WAS_DATATYPES = {
	WasBooleanDataType.TYPENAME : WasBooleanDataType(),
	WasStringDataType.TYPENAME  : WasStringDataType()
}

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
	'__TYPE__'  : None
}

class WasObjectMethodWrapper:

	def __init__(self, func, inst):
		self.func = func
		self.inst = inst
		self.__name__ = self.func.__name__

	def __call__(self, *args, **kw):
		return apply(self.func, (self.inst,) + args, kw)

class WasObjectHelper:
	
	__methodwrapper__ = WasObjectMethodWrapper
	
	def __helperinit__(self, klass):
		self.__klass__ = klass
		self.__type__  = klass.__name__
	
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
##                      WebSphere utilities                           ##
########################################################################

def was_getconfigid(id):
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
		typename = typename[0:len(typename)-1]
		return WasArrayDataType(was_type(typename))
	elif WAS_DATATYPES.has_key(typename):
		return WAS_DATATYPES[typename]
	else:
		if not WasObjectClass.__OBJ_TYPES__.has_key(typename):
			raise IllegalArgumentException, "Unknown type name: '%s'" % typename
		return WasObjectDataType(typename, WasObjectClass.__OBJ_TYPES__[typename])
