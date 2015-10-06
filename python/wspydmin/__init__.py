"""
__init__.py

Created by Antonio Alonso Domínguez on 2010-11-01.
Copyright (c) 2010 __MyCompanyName__. All rights reserved.
"""

import copy, types, re

from com.ibm.ws.scripting  import ScriptingException

class WSPydminException(Exception):
	"""
	Base root exception class for every exception inside the WSPydmin framework
	"""
	
	def __init__(self, msg):
		Exception.__init__(self, msg)

########################################################################
##                      WebSphere metaclasses                         ##
########################################################################

class WasObjectMethodWrapper:
	"""
	WAS object invocation wrapper.
	"""

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
		
		inst.__define_instance__()
		return inst

WasObject = WasObjectClass('WasObject')

########################################################################
##                      Resource Classes                              ##
########################################################################

class InvalidConfigIdError(WSPydminException):

	def __init__(self, msg):
		WSPydminException.__init__(self, msg)

class ResourceConfigId:
	
	def __init__(self, configid):
        configidRE = re.compile(r'(\w+)(\(.+\))')
        matches    = configidRE.findall(configid)
        if len(matches) > 0:
            self.resource_type = matches.group(0)
            self.resource_file = matches.group(1)
            self.resource_node = matches.group(2)
    
    def __str__(self):
        return '%s(%s#%s)' % (self.resource_type, self.resource_file, self.resource_node)

class InvalidPathIdError(WSPydminException):
	
	def __init__(self, msg):
		WSPydminException.__init__(self, msg)

class ResourcePathId:
	
	def __init__(self, pathid):
		if pathid[-1] == '/':
			pathid = pathid[:-1]
		lastSlash = pathid.lastindex('/')
		pathidRE  = re.compile(r'^\/(\w+)\:([\w\d\s]+)$')
		match     = pathidRE.match(pathid[lastSlash:])
		
		if not match:
			raise InvalidPathIdError, pathid
			
		self.type  = match.group(0)
		self.value = match.group(1)
		
		if lastSlash > 0:
			self.parent = ResourcePathId(pathid[:lastSlash])
		else:
			self.parent = None
	
	def to_condigid(self):
		pathid = str(self)
		try:
			configidStr = AdminConfig.getid(pathid).splitlines()[0]
			if configidStr is None:
				return None
			return ResourceConfigId(configidStr)
		except IndexError:
			pass
		except ScriptingException:
			pass
		return None
	
	def __str__(self):
		parentStr = ''
		if self.parent is not None:
			parentStr = str(self.parent)
		return ('%s/%s:%s') % (parentStr, self.type, self.value)

