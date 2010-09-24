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

import re, copy, logging

from java.lang             import IllegalStateException
from com.ibm.ws.scripting  import ScriptingException

from net.sf.wspydmin       import AdminConfig, AdminControl
from net.sf.wspydmin.lang  import *

__WAS_RES_DATATYPES = {
}

__WAS_RES_OBJTYPES = {
}

def __was_define_res_type(typename, typeclass):
	if __WAS_RES_DATATYPES.has_key(typename):
		raise ResourceDataTypeError, 'Type already registered: %s' % typename
	__WAS_RES_DATATYPES[typename] = typeclass()

def __was_define_res_class(klass):
	if __WAS_RES_OBJTYPES.has_key(klass.__name__):
		raise ResourceDataTypeError, 'Object class already registered: %s' % klass.__name__
	__WAS_RES_OBJTYPES[klass.__name__] = klass

def was_resource_type(typename):
	if (typename == '') or (typename is None): return None
	if typename.endswith('*'):
		typename = typename[0:-1]
		return ResourceArrayDataType(was_resource_type(typename))
	elif __WAS_RES_DATATYPES.has_key(typename):
		return __WAS_RES_DATATYPES[typename]
	else:
		if not __WAS_RES_OBJTYPES.has_key(typename):
			raise IllegalArgumentException, "Unknown type name: '%s'" % typename
		return WasObjectDataType(__WAS_RES_OBJTYPES[typename])

########################################################################
##                         WebSphere types                            ##
########################################################################

class ResourceDataTypeError(Exception):
	pass

class ResourceDataType:
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

class ResourceArrayDataType(ResourceDataType):
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

		ResourceDataType.__init__(self, element_typename + '*')
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

class BooleanDataType(ResourceDataType):
	"""
	Boolean data types handler

	@author: A. Alonso Dominguez
	"""
	TYPENAME = 'boolean'

	def __init__(self):
		"""
		Initializes the boolean data type
		"""
		ResourceDataType.__init__(self, WasBooleanDataType.TYPENAME)

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

class IntegerDataType(ResourceDataType):
	"""

	@author: A. Alonso Dominguez
	"""
	TYPENAME = 'Integer'

	def __init__(self):
		ResourceDataType.__init__(self, WasIntegerDataType.TYPENAME)

	def from_str(self, value):
		if (value == '') or (value is None): 
			return None
		return int(value)

	def to_str(self, value):
		if value is None: return ''
		return '%i' % value

class StringDataType(ResourceDataType):
	"""

	@author: A. Alonso Dominguez
	"""
	TYPENAME = 'String'

	def __init__(self):
		ResourceDataType.__init__(self, WasStringDataType.TYPENAME)

	def from_str(self, value):
		if (value == '') or (value is None): return None
		if value.startswith('"') and value.endswith('"'):
			value = value[1:-1]
		return value

	def to_str(self, value):
		if value is None: return ''
		return '"' + str(value) + '"'

class ResourceObjectDataType(ResourceDataType):
	"""

	@author: A. Alonso Dominguez
	"""

	def __init__(self, klass):
		ResourceDataType.__init__(self, klass.__name__)
		self.klass = klass

	def from_str(self, value):
		if (value == '') or (value is None): return None
		return self.klass(value)

	def to_str(self, value):
		if value is None: return ''
		return self.klass.__getconfigid__(value)

# Define WebSphere's configuration primitive types
__was_define_res_type(BooleanDataType.TYPENAME, BooleanDataType)
__was_define_res_type(IntegerDataType.TYPENAME, IntegerDataType)
__was_define_res_type(StringDataType.TYPENAME, StringDataType)



class AbstractResourceError(Exception):
	pass

class ResourceClassHelper(WasObjectClassHelper):
	
	def __helperinit__(self, klass):
		WasObjectClassHelper.__helperinit__(self, klass)
		self.__was_cfg_type__ = klass.__name__
		self.__was_cfg_attrtypes__  = {}
	
	def __define_instance__():
		attrdef = AdminConfig.attributes(self.__was_cfg_type__)
		if (attrdef is not None) and (attrdef != ''):
			for atype in attrdef.splitlines():
				name = atype.split()[0]
				value = atype.split()[1]			
				self.__was_cfgtypes[name] = was_resource_type(value)

class ResourceClass(WasObjectClass):
	__helper__ = ResourceClassHelper
	
	def __init__(self, name, bases = (), dict = {}):
		WasObjectClass.__init__(self, name, bases, dict)

class Resource(WasObject):
	__TEMPLATES         = {}
	__parent_attrname__ = 'parent'
	
	ATTR_ID    = 'DEF_CFG_PATH'
	ATTR_SCOPE = 'DEF_SCOPE'
	ATTR_ATTRS = 'DEF_CFG_ATTRS'
	ATTR_TMPL  = 'DEF_CFG_TMPL'
	
	def __init__(self):
		if not hasattr(self, Resource.ATTR_ID):
			raise AbstractResourceError, self.__was_cfg_type__

		try:	
			self.__wasattrmap = copy.copy(getattr(self, Resource.ATTR_ATTRS))
		except AttributeError:
			self.__wasattrmap = {}
		
		# Container for attribute data types
		self.__was_cfgtypes = {}		
		
	def __postinit__(self):
		
		
		self.__hydrate__()
		if self.exists():
			self.__loadattrs__()
		else:
			self.__loaddefaults__()
	
	def __create__(self, update):
		attributes = self.__collectattrs__()
		if self.exists():
			if update:
				id = self.__getconfigid__()
				logging.debug("Updating resource '%s' under scope '%s' with attributes %s." % (self.__was_cfg_type__, id.split('/')[-1].split('|')[0], attributes))
				AdminConfig.modify(id, attributes)
			else:
				logging.warn("Resource already exists '%s'. NOT UPDATED!" % self.__was_cfg_path__)
				return
		else:
			if not self.__template__ is None:
				logging.debug("Creating resource using template '%s'" % self.__template__)
				AdminConfig.createUsingTemplate(self.__was_cfg_type__, self.__scope__, attributes, self.__template__)
			else:
				AdminConfig.create(self.__was_cfg_type__, self.__scope__, attributes)
			
		if not self.exists():
			raise Exception, "Resource '%s' has not been created as expected!" % self.__was_cfg_path__
		else:
			logging.info("Created '%s' resource under scope '%s' using attrs: %s" % (self.__was_cfg_type__, scope.split('/')[-1].split('|')[0], attributes))
	
	def __collectattrs__(self):
		return [ [label, self.__flatattr__(label, value) ] for label, value in self.__wasattrmap.items() if not value is None ]
	
	def __getattr__(self, name):
		try:
			return WasObject.__getattr__(self, name)
		except AttributeError:
			if self.__wasattrmap.has_key(name):
				val = self.__wasattrmap[name]
				if val == '': val = None
				return val
			else:
				raise AttributeError, name
	
	def __setattr__(self, name, value):
		if hasattr(self, '__wasattrmap') and getattr(self, '__wasattrmap').has_key(name):
			if type("") == type(value):
				value = self.__parseattr__(name, value)
			self.__wasattrmap[name] = value
		else:
			WasObject.__setattr__(self, name, value)
	
	def __loadattrs__(self, skip_attrs = []):
		if not self.exists(): return
		for attr in AdminConfig.show(self.__getconfigid__()).splitlines():
			if not self.__wasattrmap.has_key(attr): continue
			if not self.__wasattrmap[attr] is None: continue
			if attr.startswith('[') and attr.endswith(']'):
				attr = attr[1:-1]               # Drop '[' and ']' from attribute string
			name = attr.split(None, 1)[0]
			if not skip_attrs.contains(name):
				self.__wasattrmap[name] = self.__parseattr__(name, attr.split(None, 1)[1])
	
	def __loaddefaults__(self): 
		pass
	
	def __dumpattrs__(self):
		str = ''
		if hasattr(self, '__wasattrmap') and hasattr(self, '__was_cfgtypes'):
			for name, value in self.__wasattrmap.items():
				value = self.__flatattr__(name, value)
				str = str + ("\t(%s) %s = %s\n" % (self.__was_cfgtypes[name], name, value))
		return str
	
	def __flatattr__(self, name, value):
		if not self.__was_cfgtypes.has_key(name):
			raise AttributeError, "attribute '%s' can't be flattened since no type has been found" % name
		type = self.__was_cfgtypes[name]
		return type.to_str(value)
	
	def __parseattr__(self, name, value):
		if not self.__was_cfgtypes.has_key(name):
			raise AttributeError, "attribute '%s' can't be parsed since no type has been found" % name
		type = self.__was_cfgtypes[name]
		return type.from_str(value)
	
	def __getconfigid__(self):
		id = was_getconfigid(self.__was_cfg_path__)
		if (id is None) and hasattr(self, self.__parent_attrname__):
			parent = getattr(self, self.__parent_attrname__)
			id = parent.__getconfigid__()
		return id
	
	def __hydrate__(self):
		if not hasattr(self, '__wasattrmap'):
			raise IllegalStateException, "WAS resource unproperly initialized"
		
		# Collect public WAS attributes
		mydict = {}
		map(
			lambda x: mydict.__setitem__(x, self.__wasattrmap[x]),
			filter(
				lambda x: (not x.startswith('__')),
				self.__wasattrmap.keys()
			)
		)
		
		# Resolve hydrated objet scope
		if not hasattr(self, Resource.ATTR_SCOPE):
			if hasattr(self, self.__parent_attrname__):
				parent = getattr(self, self.__parent_attrname__)
				if not hasattr(parent, '__was_cfg_path__'):
					raise IllegalStateException, "'%s' attribute must be a concrete and hydrated Resource instance" % self.__parent_attrname__
				self.__scope__ = parent.__was_cfg_path__
			else:
				self.__scope__ = AdminControl.getCell()
		else:
			if hasattr(self, self.__parent_attrname__):
				parent = getattr(self, self.__parent_attrname__)
				if hasattr(parent, '__was_cfg_path__'):
					mydict['parent'] = parent.__was_cfg_path__
			self.__scope__ = getattr(self, Resource.ATTR_SCOPE) % mydict
		mydict['scope'] = self.__scope__
		
		# Hydrate object id
		self.__was_cfg_path__ = getattr(self, Resource.ATTR_ID) % mydict
		
		# Initialize template map for this resource type
		if not Resource.__TEMPLATES.has_key(self.__was_cfg_type__):
			Resource.__TEMPLATES[self.__was_cfg_type__] = {}
			for tplid in AdminConfig.listTemplates(self.__was_cfg_type__).splitlines():
				if tplid.startswith('"') and tplid.endswith('"'):
					tplid = tplid[1:-1]
				Resource.__TEMPLATES[self.__was_cfg_type__][tplid.split('(')[0]] = tplid
		
		# Hydrate resource's template name
		template = None
		if hasattr(self, Resource.ATTR_TMPL):
			template = getattr(self, Resource.ATTR_TMPL) % mydict
		self.__settmpl__(template)
	
	def __remove__(self, deep):
		if deep:
			logging.info("Removing all %s objects..." % self.__was_cfg_type__)
			for res in AdminConfig.list(self.__was_cfg_type__).splitlines():
				AdminConfig.remove(res)
		elif self.exists():
			id = self.__getconfigid__()
			AdminConfig.remove(id)
			if self.exists():
				#raise Exception, "Resource '%s(id=%s)' under scope '%s' has not been removed as expected!" % (self.__was_cfg_type__, id.split('/')[-1].split('|')[0], id)
				raise Exception, "Resource '%s(id=%s)' under scope '%s' has not been removed as expected!" % (self.__was_cfg_type__, self.__was_cfg_path__, self.__scope__)
			else:
				#print "Resource '%s(id=%s)' under scope '%s' removed." % (self.__was_cfg_type__, self.__was_cfg_path__,  id.split('/')[-1].split('|')[0], id)
				logging.info("Resource '%s(id=%s)' under scope '%s' removed." % (self.__was_cfg_type__, self.__was_cfg_path__,  self.__scope__))
		else:
			logging.warn("Resource '%s(id=%s)' does not exist under scope '%s'. Nothing done." % (self.__was_cfg_type__, self.__was_cfg_path__, self.__scope__))
	
	def __settmpl__(self, template):
		if (template is not None) and Resource.__TEMPLATES[self.__was_cfg_type__].has_key(template):
			self.__template__ = Resource.__TEMPLATES[self.__was_cfg_type__][template]
		else:
			self.__template__ = None
	
	def __str__(self):
		if hasattr(self, '__was_cfg_type__') and hasattr(self, '__was_cfg_path__') and hasattr(self, '__scope__') and hasattr(self, '__template__'):
			str = "%s(id='%s', scope='%s', template='%s')\n" % (self.__was_cfg_type__, self.__was_cfg_path__, self.__scope__, self.__template__)
			return str + self.__dumpattrs__()
		else:
			return str(self.__wasclass__)
	
	def exists(self):
		obj = self.__getconfigid__()
		return (obj is not None)
	
	def create(self):
		self.__create__(0)
	
	def update(self):
		self.__create__(1)
	
	def remove(self):
		self.__remove__(0)
	
	def removeAll(self):
		self.__remove__(1)

