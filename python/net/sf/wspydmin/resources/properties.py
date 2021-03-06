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

import sys, copy

from net.sf.wspydmin      import AdminConfig, AdminControl
from net.sf.wspydmin.lang import Resource, was_resource_type

class J2EEPropertyHolderResource(Resource):

	def __init__(self):
		Resource.__init__(self)
		if hasattr(self, 'DEF_PROPS'):
			self.__defaults = copy.copy(getattr(self, 'DEF_PROPS'))
		else:
			self.__defaults = {}
		self.__propertySet = J2EEResourcePropertySet(self)
	
	def __create__(self, update):
		Resource.__create__(self, update)
		self.__propertySet.update()
		
	def __dumpattrs__(self):
		str = Resource.__dumpattrs__(self)
		if hasattr(self, '__propertySet'):
			for name, prop in self.__propertySet.properties():
				str = str + ("\t(%s) %s = %s\n" % (prop.type, prop.name, prop.value))
		return str
	
	def __getattr__(self, name):
		try:
			return Resource.__getattr__(self, name)
		except AttributeError:
			if hasattr(self, '__propertySet'):
				return self.getProperty(name)
			else:
				raise AttributeError, name
	
	def __setattr__(self, name, value):
		if not hasattr(self, '__propertySet'):
			Resource.__setattr__(self, name, value)
		else:
			if self.__defaults.has_key(name):
				self.setProperty(name, value)
			else:
				Resource.__setattr__(self, name, value)
	
	def getProperty(self, name):
		if not self.__defaults.has_key(name):
			raise AttributeError, name
		return self.__propertySet.getProperty(name, self.__defaults[name])
	
	def setProperty(self, name, value):
		if not self.__defaults.has_key(name):
			raise AttributeError, name
		self.__propertySet.addProperty(name, value)

class PropertyHolderResource(Resource):
	
	def __init__(self):
		Resource.__init__(self)
		self.__properties = {}
	
	def __create__(self, update):
		Resource.__create__(self, update)
		for name, prop in self.__properties.items():
			prop.__create__(update)
	
	def __collectattrs__(self):
		attrs = self.__wassuper__.__collectattrs__(self)
		props = []
		for name, prop in self.__properties__.items():
			props.append( [ name, prop.value ] )
		attrs.append( props )
		return attrs
	
	def __getattr__(self, name):
		try:
			return Resource.__getattr__(self, name)
		except AttributeError:
			if hasattr(self, '__properties'):
				if self.__properties.has_key(name):
					return self.__properties[name].value
			raise AttributeError, name
	
	def __setattr__(self, name, value):
		if not hasattr(self, '__properties'):
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
		if hasattr(self, '__properties'):
			for prop in self.__properties.values():
				str = str + ("\t(unknown) %s = %s\n" % (prop.name, prop.value))
		return str

	def addProperty(self, name, value = None, description = None, required = 0, validationExpr = None):
		prop                      = Property(name)
		prop.value                = value
		prop.description          = description
		prop.required             = required
		prop.validationExpression = validationExpr
		self.__properties[name]   = prop
		
	def getProperty(self, name):
		if not self.__properties.has_key(name):
			raise AttributeError, name
		return self.__properties[name]
	
	def setProperty(self, name, value):
		if not self.__properties.has_key(name):
			raise AttributeError, name
		self.__properties[name].value = value

class Property(Resource):
	DEF_CFG_PATH    = '%(scope)sProperty:%(name)s/'
	DEF_CFG_ATTRS = {
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
		for pid in AdminConfig.list(Property.__was_cfg_type__, self.parent.__getconfigid__()).splitlines():
			if pid.startswith(self.name):
				return pid
		return None

class J2EEResourceProperty(Resource):
	DEF_CFG_PATH    = '%(scope)sJ2EEResourceProperty:/'
	DEF_CFG_ATTRS = {
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
		for p in AdminConfig.getid(self.__was_cfg_path__).splitlines():
			if self.name == p.split('(')[0]:
				return p
		return None

	def __setattr__(self, name, value):
		if name == 'type':
			value = was_resource_type(value)
		Resource.__setattr__(self, name, value)

class J2EEResourcePropertySet(Resource):
	DEF_CFG_PATH    = '%(scope)sJ2EEResourcePropertySet:/'
	DEF_CFG_ATTRS = {}

	def __init__(self, parent):
		Resource.__init__(self)
		self.__propset = {} # A hash as a container for the J2EE Properties
		self.parent    = parent
	
	def __create__(self, update):
		Resource.__create__(self, update)
		for name, prop in self.__propset.items():
			prop.__create__(update)
	
	def addProperty(self, name, value, type = None, required = None, desc = None):
		property             = J2EEResourceProperty(self)
		property.name        = name
		property.value       = value
		property.type        = type
		property.required    = required
		property.description = desc
		self.__propset[name] = prop
	
	def getProperty(self, name, default = None):
		try:
			return self.__propset[name].value
		except KeyError:
			return default
	
	def properties(self):
		return copy.copy(self.__propset)
