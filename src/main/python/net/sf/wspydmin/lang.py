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

from java.lang             import Class as JavaClass, Array as JavaArray, Exception, IllegalArgumentException
from com.ibm.ws.scripting  import ScriptingException
from net.sf.wspydmin       import AdminConfig, Help

def java_type(typename):
	if (typename == '') or (typename is None): return None
	if typename.startswth('java.'):
		return JavaClass.forName(typename)
	if typename.startswith('[L'):
		elementType = java_type(typename[2:-1])
		return JavaArray.new(elementType, 0).getClass()
	return None

########################################################################
##                      WebSphere metaclasses                         ##
########################################################################

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
			return ga(self, name)
		
		if type(raw) != types.FunctionType:
			return raw
		return self.__methodwrapper__(raw, self)
	
	def __define_instance__(self):
		pass
	
	def __missedattr__(self, name):
		raise AttributeError, name

class WasObjectClass:
	__helper__    = WasObjectClassHelper
	__inited      = 0

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
		
		try:
			init = getattr(inst, '__init__')
			apply(init, args, kw)
		except AttributeError:
			pass
		
		inst.__define_instance()
		
		try:
			post = getattr(inst, '__postinit__')
			apply(post, (inst,), {})
		except AttributeError:
			pass
		
		return inst

##
# Base WAS object class which should be used as the
# primary super class for any WAS instance
__WasObject = WasObjectClass('WasObject')

class WasObject(__WasObject):
	
	def __init__(self):
		pass

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
