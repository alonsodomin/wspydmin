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
from net.sf.wspydmin.lang  import WasObject, was_getconfigid
from net.sf.wspydmin.types import *

class AbstractResourceError(Exception):
	pass

class Resource(WasObject):
	__TEMPLATES         = {}
	__parent_attrname__ = 'parent'
	
	ATTR_ID    = 'DEF_ID'
	ATTR_SCOPE = 'DEF_SCOPE'
	ATTR_ATTRS = 'DEF_ATTRS'
	ATTR_TPL   = 'DEF_TPL'
	
	def __init__(self):
		if not hasattr(self, Resource.ATTR_ID):
			raise AbstractResourceError, self.__wastype__

		try:	
			self.__wasattrmap = copy.copy(getattr(self, Resource.ATTR_ATTRS))
		except AttributeError:
			self.__wasattrmap = {}
		
		# Container for attribute data types
		self.__wastypemap = {}		
		
	def __postinit__(self):
		attrdef = AdminConfig.attributes(self.__wastype__)
		if (attrdef is not None) and (attrdef != ''):
			for atype in attrdef.splitlines():
				name = atype.split()[0]
				value = atype.split()[1]			
				self.__wastypemap[name] = was_type(value)
		
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
				logging.debug("Updating resource '%s' under scope '%s' with attributes %s." % (self.__wastype__, id.split('/')[-1].split('|')[0], attributes))
				AdminConfig.modify(id, attributes)
			else:
				logging.warn("Resource already exists '%s'. NOT UPDATED!" % self.__id__)
				return
		else:
			if not self.__template__ is None:
				logging.debug("Creating resource using template '%s'" % self.__template__)
				AdminConfig.createUsingTemplate(self.__wastype__, self.__scope__, attributes, self.__template__)
			else:
				AdminConfig.create(self.__wastype__, self.__scope__, attributes)
			
		if not self.exists():
			raise Exception, "Resource '%s' has not been created as expected!" % self.__id__
		else:
			logging.info("Created '%s' resource under scope '%s' using attrs: %s" % (self.__wastype__, scope.split('/')[-1].split('|')[0], attributes))
	
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
			if attr.startswith('[') and attr.endswith(']'):
				attr = attr[1:-1]               # Drop '[' and ']' from attribute string
			name = attr.split(None, 1)[0]
			if not skip_attrs.contains(name):
				self.__wasattrmap[name] = self.__parseattr__(name, attr.split(None, 1)[1])
	
	def __loaddefaults__(self): 
		pass
	
	def __dumpattrs__(self):
		str = ''
		if hasattr(self, '__wasattrmap') and hasattr(self, '__wastypemap'):
			for name, value in self.__wasattrmap.items():
				value = self.__flatattr__(name, value)
				str = str + ("\t(%s) %s = %s\n" % (self.__wastypemap[name], name, value))
		return str
	
	def __flatattr__(self, name, value):
		if not self.__wastypemap.has_key(name):
			raise AttributeError, "attribute '%s' can't be flattened since no type has been found" % name
		type = self.__wastypemap[name]
		return type.to_str(value)
	
	def __parseattr__(self, name, value):
		if not self.__wastypemap.has_key(name):
			raise AttributeError, "attribute '%s' can't be parsed since no type has been found" % name
		type = self.__wastypemap[name]
		return type.from_str(value)
	
	def __getconfigid__(self):
		id = was_getconfigid(self.__id__)
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
				if not hasattr(parent, '__id__'):
					raise IllegalStateException, "'%s' attribute must be a concrete and hydrated Resource instance" % self.__parent_attrname__
				self.__scope__ = parent.__id__
			else:
				self.__scope__ = AdminControl.getCell()
		else:
			if hasattr(self, self.__parent_attrname__):
				parent = getattr(self, self.__parent_attrname__)
				if hasattr(parent, '__id__'):
					mydict['parent'] = parent.__id__
			self.__scope__ = getattr(self, Resource.ATTR_SCOPE) % mydict
		mydict['scope'] = self.__scope__
		
		# Hydrate object id
		self.__id__ = getattr(self, Resource.ATTR_ID) % mydict
		
		# Initialize template map for this resource type
		if not Resource.__TEMPLATES.has_key(self.__wastype__):
			Resource.__TEMPLATES[self.__wastype__] = {}
			for tplid in AdminConfig.listTemplates(self.__wastype__).splitlines():
				if tplid.startswith('"') and tplid.endswith('"'):
					tplid = tplid[1:-1]
				Resource.__TEMPLATES[self.__wastype__][tplid.split('(')[0]] = tplid
		
		# Hydrate resource's template name
		template = None
		if hasattr(self, Resource.ATTR_TPL):
			template = getattr(self, Resource.ATTR_TPL) % mydict
		self.__settmpl__(template)
	
	def __remove__(self, deep):
		if deep:
			logging.info("Removing all %s objects..." % self.__wastype__)
			for res in AdminConfig.list(self.__wastype__).splitlines():
				AdminConfig.remove(res)
		elif self.exists():
			id = self.__getconfigid__()
			AdminConfig.remove(id)
			if self.exists():
				#raise Exception, "Resource '%s(id=%s)' under scope '%s' has not been removed as expected!" % (self.__wastype__, id.split('/')[-1].split('|')[0], id)
				raise Exception, "Resource '%s(id=%s)' under scope '%s' has not been removed as expected!" % (self.__wastype__, self.__id__, self.__scope__)
			else:
				#print "Resource '%s(id=%s)' under scope '%s' removed." % (self.__wastype__, self.__id__,  id.split('/')[-1].split('|')[0], id)
				logging.info("Resource '%s(id=%s)' under scope '%s' removed." % (self.__wastype__, self.__id__,  self.__scope__))
		else:
			logging.warn("Resource '%s(id=%s)' does not exist under scope '%s'. Nothing done." % (self.__wastype__, self.__id__, self.__scope__))
	
	def __settmpl__(self, template):
		if (template is not None) and Resource.__TEMPLATES[self.__wastype__].has_key(template):
			self.__template__ = Resource.__TEMPLATES[self.__wastype__][template]
		else:
			self.__template__ = None
	
	def __str__(self):
		if hasattr(self, '__wastype__') and hasattr(self, '__id__') and hasattr(self, '__scope__') and hasattr(self, '__template__'):
			str = "%s(id='%s', scope='%s', template='%s')\n" % (self.__wastype__, self.__id__, self.__scope__, self.__template__)
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

