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

import sys, copy

from net.sf.wspydmin           import AdminConfig, AdminControl
from net.sf.wspydmin.resources import Resource

class J2EEPropertySetResource(Resource):

	def __init__(self):
		Resource.__init__(self)
		self.__defaults__    = copy.copy(getattr(self, 'DEF_PROPS'))
		self.__propertySet__ = J2EEResourcePropertySet(self)
	
	def __create__(self, update):
		Resource.__create__(self, update)
		self.__propertySet__.update()
	
	def __dumpattrs__(self):
		str = Resource.__dumpattrs__(self)
		if hasattr(self, '__propertySet__'):
			for name, prop in self.__propertySet__.properties():
				str = str + ("\t(%s) %s = %s\n" % (prop.type, prop.name, prop.value))
		return str
	
	def __getattr__(self, name):
		try:
			return Resource.__getattr__(self, name)
		except AttributeError:
			if hasattr(self, '__propertySet__'):
				return self.getProperty(name)
			else:
				raise AttributeError, name
	
	def __setattr__(self, name, value):
		if not hasattr(self, '__propertySet__'):
			Resource.__setattr__(self, name, value)
		else:
			if self.__defaults__.has_key(name):
				self.setProperty(name, value)
			else:
				Resource.__setattr_(self, name, value)
	
	def getProperty(self, name):
		if not self.__defaults__.has_key(name):
			raise AttributeError, name
		return self.__propertySet__.getProperty(name, self.__defaults__[name])
	
	def setProperty(self, name, value):
		if not self.__defaults__.has_key(name):
			raise AttributeError, name
		self.__propertySet__.addProperty(name, value)

class PropertySetResource(Resource):
	def __init__(self):
		Resource.__init__(self)
		self.__properties__ = {}
	
	def __getattr__(self, name):
		try:
			return Resource.__getattr__(self, name)
		except AttributeError:
			if hasattr(self, '__properties__'):
				if self.__properties.__has_key(name):
					return self.__properties__[name].value
			raise AttributeError, name
	
	def __setattr__(self, name, value):
		if not hasattr(self, '__properties__'):
			Resource.__setattr__(self, name, value)
		else:
			try:
				Resource.__getattr__(self, name)
			except AttributeError:
				self.setProperty(name, value)
			else:
				Resource.__setattr__(self, name, value)
	
	def __dumpattrs__(self):
		str = Resource.__dumpattrs__(self)
		if hasattr(self, '__properties__'):
			for prop in self.__properties__.values():
				str = str + ("\t(unknown) %s = %s\n" % (prop.name, prop.value))
		return str

	def addProperty(self, name, value = None, description = None, required = 0, validationExpr = None):
		prop                      = Property(name)
		prop.value                = value
		prop.description          = description
		prop.required             = required
		prop.validationExpression = validationExpr
		self.__properties__[name] = prop
		
	def getProperty(self, name):
		if not self.__properties__.has_key(name):
			raise AttributeError, name
		return self.__properties__[name]
	
	def setProperty(self, name, value):
		if not self.__properties__.has_key(name):
			raise AttributeError, name
		self.__properties__[name].value = value

class Property(Resource):
	DEF_SCOPE = None # Provided
	DEF_ID    = '%(scope)sProperty:%(name)s/'
	DEF_TPL   = None
	DEF_ATTRS = {
                        'name' : None,
                       'value' : None,
                 'description' : None,
                    'required' : None,
        'validationExpression' : None
	}
	
	def __init__(self, name, parent):
		Resource.__init__(self)
		self.name   = name
		self.parent = parent
	
	def __getconfigid__(self):
		for pid in AdminConfig.list(Property.__type__, self.parent.__getconfigid__()).splitlines():
			if pid.startswith(self.__attrmap__['name']):
				return pid
		return None

class J2EEResourceProperty(Resource):
	DEF_SCOPE = None # Provided
	DEF_ID    = '%(scope)sJ2EEResourceProperty:/'
	DEF_TPL   = None
	DEF_ATTRS = {
             'name' : None,
             'type' : None,
            'value' : None,
      'description' : None,
         'required' : None
	}
	
	def __init__(self, parent):
		Resource.__init__(self)
		self.parent = parent
	
	def __getconfigid__(self):
		for p in AdminConfig.getid(self.__id__).splitlines():
			if self.__attrmap__['name'] == p.split('(')[0]:
				return p
		return None

	def set(self, name, value):
		self.name = name
		self.value = value
		self.__hydrate__()

class J2EEResourcePropertySet(Resource):
	DEF_SCOPE = None # Provided
	DEF_ID    = '%(scope)sJ2EEResourcePropertySet:/'
	DEF_TPL   = None
	DEF_ATTRS = {}

	def __init__(self, parent):
		Resource.__init__(self)
		self.__propset__ = {} # A hash as a container for the J2EE Properties
		self.parent      = parent
	
	def __create__(self, update):
		Resource.__create__(self, update)
		for name, prop in self.__propset__.items():
			prop.__create__(update)
	
	def addProperty(self, name, value, type = None, required = None, desc = None):
		p = J2EEResourceProperty(self)
		p.set(name, value)
		p.type = type
		p.required = required
		p.description = desc
		self.__propset__[name] = p
	
	def getProperty(self, name, default = None):
		try:
			return self.__propset__[name].value
		except KeyError:
			return default
	
	def properties(self):
		return copy.copy(self.__propset__)
