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

import re, copy

from com.ibm.ws.scripting import ScriptingException

from net.sf.wspydmin      import AdminConfig, AdminControl
from net.sf.wspydmin.lang import *

class AbstractResourceError(Exception):
	pass

class Resource(WasObject):
	__TEMPLATES__ = {}
	
	def __init__(self):
		if not hasattr(self, 'DEF_ID'):
			raise AbastractResourceError, self.__type__

		self.__id__ = getattr(self, 'DEF_ID')
		try:
			self.__scope__ = getattr(self, 'DEF_SCOPE')
		except AttributeError:
			self.__scope__ = None

		try:	
			self.__attrmap__ = copy.copy(getattr(self, 'DEF_ATTRS'))
		except AttributeError:
			self.__attrmap__ = {}
		
		# Container for attribute data types
		self.__typemap__ = {}
		
		try:
			template = getattr(self, 'DEF_TPL')
			self.__settmpl__(template)
		except AttributeError:
			self.__template__ = None
		
	def __postinit__(self):
		if self.__type__ is None: return
		print "Processing attribute types"
		attrdef = AdminConfig.attributes(self.__type__)
		if (attrdef is not None) and (attrdef != ''):
			for atype in attrdef.splitlines():
				name = atype.split()[0]
				value = atype.split()[1]			
				self.__typemap__[name] = was_type(value)
		
		print "Assembling instance"
		self.__hydrate__()
		if self.exists():
			print "Loading was data"
			self.__loadattrs__()
		else:
			print "Loading default data"
			self.__loaddefaults__()
	
	def __create__(self, update):
		attributes = self.__collectattrs__()
		if self.exists():
			if update:
				id = self.__getconfigid__()
				print "Updating resource '%s' under scope '%s' with attributes %s." % (self.__type__, id.split('/')[-1].split('|')[0], attributes)
				AdminConfig.modify(id, attributes)
			else:
				print "WARN: resource already exists '%s'. NOT UPDATED!" % self.__id__
				return
		else:
			if self.__scope__.startswith('/'): #Weird! TO REFACTOR!
				if hasattr(self, 'parent'):
					scope = self.parent.__getconfigid__()
				else:
					scope = was_getconfigid(self.__scope__)
			else:
				scope = self.__scope__
			
			if not self.__template__ is None:
				print "Creating resource using template '%s'" % self.__template__
				AdminConfig.createUsingTemplate(self.__type__, scope, attributes, self.__template__)
			else:
				AdminConfig.create(self.__type__, scope, attributes)
			
			print "Created '%s' resource under scope '%s' using attrs: %s" % (self.__type__, scope.split('/')[-1].split('|')[0], attributes)
			
		if not self.exists():
			raise Exception, "Resource '%s' has not been created as expected!" % self.__id__
	
	def __collectattrs__(self):
		return [ [label, self.__flatattr__(label, value) ] for label, value in self.__attrmap__.items() if not value is None ]
	
	def __getattr__(self, name):
		try:
			return WasObject.__getattr__(self, name)
		except AttributeError:
			if self.__attrmap__.has_key(name):
				val = self.__attrmap__[name]
				if val == '': val = None
				return val
			else:
				raise AttributeError, name
	
	def __setattr__(self, name, value):
		if hasattr(self, '__attrmap__') and getattr(self, '__attrmap__').has_key(name):
			if type("") == type(value):
				value = self.__parseattr__(name, value)
			self.__attrmap__[name] = value
		else:
			WasObject.__setattr__(self, name, value)
	
	def __loadattrs__(self):
		if not self.exists(): return
		for attr in AdminConfig.show(self.__getconfigid__()).splitlines():
			attr = attr[1:len(attr)-1]          # Drop '[' and ']' from attribute string
			name = attr.split(None, 1)[0]
			self.__attrmap__[name] = self.__parseattr__(name, attr.split(None, 1)[1])
	
	def __loaddefaults__(self): 
		pass
	
	def __dumpattrs__(self):
		str = ''
		if hasattr(self, '__attrmap__') and hasattr(self, '__typemap__'):
			for name, value in self.__attrmap__.items():
				value = self.__flatattr__(name, value)
				str = str + ("\t(%s) %s = %s\n" % (self.__typemap__[name], name, value))
		return str
	
	def __flatattr__(self, name, value):
		if not self.__typemap__.has_key(name):
			raise AttributeError, "attribute '%s' can't be flattened since no type has been found" % name
		type = self.__typemap__[name]
		return type.to_str(value)
	
	def __parseattr__(self, name, value):
		if not self.__typemap__.has_key(name):
			raise AttributeError, "attribute '%s' can't be parsed since no type has been found" % name
		type = self.__typemap__[name]
		return type.from_str(value)
	
	def __getconfigid__(self):
		return was_getconfigid(self.__id__)
	
	def __hydrate__(self):
		if hasattr(self, 'parent') and (self.__scope__ is None):
			self.__scope__ = getattr(self, 'parent').__id__
		if hasattr(self, 'name') and hasattr(self, 'DEF_ID'):
			self.__id__ = self.DEF_ID % {'scope': self.__scope__, 'name': getattr(self, 'name')}
	
	def __remove__(self, deep):
		if deep:
			print "Removing all %s objects..." % self.__type__
			for res in AdminConfig.list(self.__type__).splitlines():
				AdminConfig.remove(res)
		elif self.exists():
			id = self.__getconfigid__()
			AdminConfig.remove(id)
			if self.exists():
				raise Exception, "Resource '%s' under scope '%s' has not been removed as expected! (id: %s)" % (self.__type__, id.split('/')[-1].split('|')[0], id)
			else:
				print "Resource '%s' under scope '%s' removed (id: %s)." % (self.__type__, id.split('/')[-1].split('|')[0], id)
		else:
			print "WARN: resource '%s' does not exist. Nothing done." % self.__id__
	
	def __settmpl__(self, template):
		if not Resource.__TEMPLATES__.has_key(self.__type__):
			Resource.__TEMPLATES__[self.__type__] = {}
			for tplid in AdminConfig.listTemplates(self.__type__).splitlines():
				if tplid.startswith('"') and tplid.endswith('"'):
					tplid = tplid[1:-1]
				Resource.__TEMPLATES__[self.__type__][tplid.split('(')[0]] = tplid
		
		if Resource.__TEMPLATES__[self.__type__].has_key(template):
			self.__template__ = Resource.__TEMPLATES__[self.__type__][template]
		else:
			self.__template__ = None
	
	def __str__(self):
		if hasattr(self, '__type__') and hasattr(self, '__id__') and hasattr(self, '__scope__') and hasattr(self, '__template__'):
			str = "%s(id='%s', scope='%s', template='%s')\n" % (self.__type__, self.__id__, self.__scope__, self.__template__)
			return str + self.__dumpattrs__()
		else:
			return str(self.__klass__)
	
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

class MBeanMethodInvoker:
	def __init__(self, mbeanId, methodName):
		self.mbeanId    = mbeanId
		self.methodName = methodName
	
	def __call__(self, *args, **kwargs):
		AdminControl.invoke(self.mbeanId, self.methodName, self.__parseargs__(args, kwargs))
	
	def __parseargs__(self, *args, **kwargs):
		return str(args)

class MBeanHelper(WasObjectHelper):
	__mbeaninvoker__ = MBeanMethodInvoker
	
	def __helperinit__(self, klass):
		WasObjectHelper.__helperinit__(self, klass)
		self.__methods__ = copy.copy(getattr(klass, 'DEF_MTHDS'))
	
	def __missedattr__(self, name):
		if (self.__methods__.count(name) > 0):
			return self.__mbeaninvoker__(self.__getmbeanid__(), name)
		else:
			return WasObjectHelper.__missedattr__(self, name)

class MBeanClass(WasObjectClass):
	__helper__       = MBeanHelper
	
	def __init__(self, name, bases = (), metadict = WAS_METADATA_EMPTY):
		WasObjectClass.__init__(self, name, bases, metadict)

MBean = MBeanClass('MBean', (Resource,))

class DefaultMBean(MBean):
		
	def __getmbeanid__(self):
		if hasattr(self, 'name') and hasattr(self, 'nodeName') and hasattr(self, 'serverName'):
			query = 'type=%s,name=%s,node=%s,process=%s,*' % (self.__type__, self.name, self.nodeName, self.serverName)
			return AdminControl.queryNames(query).splitlines()[0]
		else:
			raise NotImplementedError, "Please, provide an implementation of '%s.__getmbeanid__()' to consolidate the MBean binding." % self.__class__
