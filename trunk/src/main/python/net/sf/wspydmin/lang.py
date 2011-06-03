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

import copy, types, re

from java.lang             import Class as JavaClass, Array as JavaArray, Exception as JavaException, IllegalArgumentException
from com.ibm.ws.scripting  import ScriptingException
from net.sf.wspydmin       import *

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
			else:
				return ga(self, name)
		else:
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
		
		__was_define_class(self)
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
		
		try:
			post = getattr(inst, '__wasinit__')
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
##                      Resource Classes                              ##
########################################################################

class AbstractResourceError(Exception):
	pass

class ResourcePathID:
	
	def __init__(self, elem_type, elem_name, parent_path = None):
		self.elem_type   = elem_type
		self.elem_name   = elem_name
		self.parent_path = parent_path
	
	def __str__(self):
		str = ''
		if not self.parent_path is None:
			str = self.parent_path.__str__()
		str += ('/%s:%s' % (self.elem_type, self.elem_name))
		return str

class ResourceConfigID:
    
    __STR_PATTERN = '%(name)s(%(path)s|%(file)s#%(node)s)'
    
    def __init__(self, configid):
    	if configid is None or configid == '':
    		raise IllegalArgumentException, "'configid' can't be null"
    	
        configidRE = re.compile(r'(.+)\((.+)\|(.+)\#(.+)\)')
        matches    = configidRE.findall(configid)
        if len(matches) > 0:
            self.name = matches.group(0)
            self.path = matches.group(1)
            self.file = matches.group(2)
            self.node = matches.group(3)
    
    def __str__(self):
        return ResourceConfigID.__STR_PATTERN % self.__dict__

class ResourceClassHelper(WasObjectClassHelper):
	
	def __helperinit__(self, klass):
		WasObjectClassHelper.__helperinit__(self, klass)
		self.__wasclass__.__was_cfg_type__       = klass.__name__
		self.__wasclass__.__was_cfg_attrtypes__  = {}
	
	def __define_instance__():
		attrdef = AdminConfig.attributes(self.__wasclass__.__was_cfg_type__)
		if (attrdef is not None) and (attrdef != ''):
			for atype in attrdef.splitlines():
				name = atype.split()[0]
				value = atype.split()[1]			
				self.__wasclass__.__was_cfg_attrtypes__[name] = was_type(value)

class ResourceClass(WasObjectClass):
	__helper__ = ResourceClassHelper
	
	def __init__(self, name, bases = (), dict = {}):
		WasObjectClass.__init__(self, name, bases, dict)

__Resource = ResourceClass('__Resource', (WasObject,))

class Resource(__Resource):
	__TEMPLATES         = {}
	__parent_attrname__ = 'parent'
	
	ATTR_PATH    = 'DEF_CFG_PATH'
	ATTR_PARENT  = 'DEF_CFG_PARENT'
	ATTR_ATTRS   = 'DEF_CFG_ATTRS'
	ATTR_TMPL    = 'DEF_CFG_TMPL'
	
	def __init__(self):
		if not hasattr(self, Resource.ATTR_PATH):
			raise AbstractResourceError, self.__was_cfg_type__

		try:	
			self.__was_cfg_attrmap = copy.copy(getattr(self, Resource.ATTR_ATTRS))
		except AttributeError:
			self.__was_cfg_attrmap = {}
		
	def __wasinit__(self):
		self.__hydrate__()
		attrvalues = []
		if self.exists():
			attrvalues = AdminConfig.show(self.__getconfigid__()).splitlines()
		else:
			attrvalues = AdminConfig.defaults(self.__was_cfg_type__).splitlines()
		for attr in attrvalues:
			if not self.__was_cfg_attrmap.has_key(attr): continue
			if not self.__was_cfg_attrmap[attr] is None: continue
			if attr.startswith('[') and attr.endswith(']'):
				attr = attr[1:-1]               # Drop '[' and ']' from attribute string
			name = attr.split(None, 1)[0]
			if not skip_attrs.contains(name):
				self.__was_cfg_attrmap[name] = self.__parseattr__(name, attr.split(None, 1)[1])
	
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
			if not self.__was_cfg_template__ is None:
				logging.debug("Creating resource using template '%s'" % self.__was_cfg_template__)
				AdminConfig.createUsingTemplate(self.__was_cfg_type__, self.__was_cfg_parent__, attributes, self.__was_cfg_template__)
			else:
				AdminConfig.create(self.__was_cfg_type__, self.__was_cfg_parent__, attributes)
			
		if not self.exists():
			raise Exception, "Resource '%s' has not been created as expected!" % self.__was_cfg_path__
		else:
			logging.info("Created '%s' resource under scope '%s' using attrs: %s" % (self.__was_cfg_type__, scope.split('/')[-1].split('|')[0], attributes))
	
	def __collectattrs__(self):
		return [ [label, self.__flatattr__(label, value) ] for label, value in self.__was_cfg_attrmap.items() if not value is None ]
	
	def __getattr__(self, name):
		try:
			return __Resource.__getattr__(self, name)
		except AttributeError:
			if self.__was_cfg_attrmap.has_key(name):
				val = self.__was_cfg_attrmap[name]
				if val == '': val = None
				return val
			else:
				raise AttributeError, name
	
	def __setattr__(self, name, value):
		if hasattr(self, '__was_cfg_attrmap') and getattr(self, '__was_cfg_attrmap').has_key(name):
			if type("") == type(value):
				value = self.__parseattr__(name, value)
			self.__was_cfg_attrmap[name] = value
		else:
			__Resource.__setattr__(self, name, value)
	
	def __dumpattrs__(self):
		str = ''
		if hasattr(self, '__was_cfg_attrmap') and hasattr(self, '__was_cfg_attrtypes__'):
			for name, value in self.__was_cfg_attrmap.items():
				value = self.__flatattr__(name, value)
				str = str + ("\t(%s) %s = %s\n" % (self.__was_cfg_attrtypes__[name], name, value))
		return str
	
	def __flatattr__(self, name, value):
		if not self.__was_cfg_attrtypes__.has_key(name):
			raise AttributeError, "attribute '%s' can't be flattened since no type has been found" % name
		type = self.__was_cfg_attrtypes__[name]
		return type.to_str(value)
	
	def __parseattr__(self, name, value):
		if not self.__was_cfg_attrtypes__.has_key(name):
			raise AttributeError, "attribute '%s' can't be parsed since no type has been found" % name
		type = self.__was_cfg_attrtypes__[name]
		return type.from_str(value)
	
	def __getconfigid__(self):
		id = was_getconfigid(self.__was_cfg_path__)
		if (id is None) and hasattr(self, self.__parent_attrname__):
			parent = getattr(self, self.__parent_attrname__)
			id = parent.__getconfigid__()
		else:
			id = ResourceConfigID(id)
		return id
	
	def __hydrate__(self):
		if not hasattr(self, '__was_cfg_attrmap'):
			raise IllegalStateException, "WAS resource unproperly initialized"
		
		# Collect public WAS attributes
		mydict = {}
		map(
			lambda x: mydict.__setitem__(x, self.__was_cfg_attrmap[x]),
			filter(
				lambda x: (not x.startswith('__')),
				self.__was_cfg_attrmap.keys()
			)
		)
		
		# Resolve hydrated objet scope
		if not hasattr(self, Resource.ATTR_SCOPE):
			if hasattr(self, self.__parent_attrname__):
				parent = getattr(self, self.__parent_attrname__)
				if not hasattr(parent, '__was_cfg_path__'):
					raise IllegalStateException, "'%s' attribute must be a concrete and hydrated Resource instance" % self.__parent_attrname__
				self.__was_cfg_parent__ = parent.__was_cfg_path__
			else:
				self.__was_cfg_parent__ = AdminControl.getCell()
		else:
			if hasattr(self, self.__parent_attrname__):
				parent = getattr(self, self.__parent_attrname__)
				if hasattr(parent, '__was_cfg_path__'):
					mydict['parent'] = parent.__was_cfg_path__
			self.__was_cfg_parent__ = getattr(self, Resource.ATTR_SCOPE) % mydict
		mydict['scope'] = self.__was_cfg_parent__
		
		# Hydrate object id
		self.__was_cfg_path__ = getattr(self, Resource.ATTR_PATH) % mydict
		
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
				raise Exception, "Resource '%s(id=%s)' under scope '%s' has not been removed as expected!" % (self.__was_cfg_type__, self.__was_cfg_path__, self.__was_cfg_parent__)
			else:
				#print "Resource '%s(id=%s)' under scope '%s' removed." % (self.__was_cfg_type__, self.__was_cfg_path__,  id.split('/')[-1].split('|')[0], id)
				logging.info("Resource '%s(id=%s)' under scope '%s' removed." % (self.__was_cfg_type__, self.__was_cfg_path__,  self.__was_cfg_parent__))
		else:
			logging.warn("Resource '%s(id=%s)' does not exist under scope '%s'. Nothing done." % (self.__was_cfg_type__, self.__was_cfg_path__, self.__was_cfg_parent__))
	
	def __settmpl__(self, template):
		if (template is not None) and Resource.__TEMPLATES[self.__was_cfg_type__].has_key(template):
			self.__was_cfg_template__ = Resource.__TEMPLATES[self.__was_cfg_type__][template]
		else:
			self.__was_cfg_template__ = None
	
	def __str__(self):
		if hasattr(self, '__was_cfg_type__') and hasattr(self, '__was_cfg_path__') and hasattr(self, '__was_cfg_parent__') and hasattr(self, '__was_cfg_template__'):
			str = "%s(id='%s', scope='%s', template='%s')\n" % (self.__was_cfg_type__, self.__was_cfg_path__, self.__was_cfg_parent__, self.__was_cfg_template__)
			return str + self.__dumpattrs__()
		else:
			return str(self.__wasclass__)
	
	def getMBeanName(self):
		return MBeanName(AdminConfig.getObjectName(self.__getconfigid__()))
	
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


def was_resource_pathid(pathid):
	pass

########################################################################
##                         MBean Classes                              ##
########################################################################

class MBeanName:
	
	def __init__(self, objectName):
		objNameRE = re.compile(r'(?P<domainName>=\w+)\:((?P<name>=[\w|\d]+)=(?P<value>=[\w|\s|\d]+),?)+')
		matches   = objNameRE.findall(objectName)
		if len(matches) > 0:
			self.__dict__['domainName'] = matches.group('domainName')
			for name, value in matches.group(1).groups():
				self.__dict__[name] = value
	
	def __str__(self):
		result = ''
		count = 0
		for name, value in self.__dict__.items():
			if name == 'domainName': continue
			count = count + 1
			if count > 0: result += ','
			result = '%s%(name)s=%(value)s' % { 'name' : name, 'value' : value }
		result = '%s:%s' % (self.domainName, result)
		return result

class MBeanMethodInvoker:
    def __init__(self, mbeanId, methodName):
        self.mbeanId    = mbeanId
        self.methodName = methodName
    
    def __call__(self, *args, **kwargs):
        AdminControl.invoke(self.mbeanId, self.methodName, self.__parseargs__(args, kwargs))
    
    def __parseargs__(self, *args, **kwargs):
        return str(args)

class MBeanClassHelper(WasObjectClassHelper):
    
    def __helperinit__(self, klass):
        WasObjectClassHelper.__helperinit__(self, klass)
        self.__methods = copy.copy(getattr(klass, 'DEF_METHODS'))

    def __getmbeanid__(self):
        if hasattr(self, 'name') and hasattr(self, 'nodeName') and hasattr(self, 'serverName'):
            query = 'type=%s,name=%s,node=%s,process=%s,*' % (self.__was_cfg_type__, self.name, self.nodeName, self.serverName)
            return AdminControl.queryNames(query).splitlines()[0]
        else:
            raise NotImplementedError, "Please, provide an implementation of '%s.__getmbeanid__()' to consolidate the MBean binding." % self.__wasclass__

	def __define_instance__(self):
		# Stablish the MBean 'real' class
		self.__mbeanclass__ = JavaClass.forName(Help.classname(self.__getmbeanid__()))
		
		# Obtain MBean's attribute definitions
		attrData = {}
		attr_pattern = re.compile(r'^([\w|\d]+)(?:\s+)([\w|\d|\.]+)(?:\s+)([RO|RW])$', re.MULTILINE)
		helpData = Help.attributes(self.__getmbeanid__())
		attrDesc = attr_pattern.findall(helpData)
		for name, datatype, access in attrDesc:
			attrDef = {
				'name'   : name,
				'type'   : datatype,
				'access' : access
			}
			attrData[name] = attrDef
		setattr(self, '__attrdef__', attrData)
    
    def __missedattr__(self, name):
        if (self.__methods.count(name) > 0):
            return MBeanMethodInvoker(self.__getmbeanid__(), name)
        else:
            return WasObjectClassHelper.__missedattr__(self, name)

class MBeanClass(WasObjectClass):
    __helper__       = MBeanClassHelper
    
    def __init__(self, name, bases = (), dict = {}):
        WasObjectClass.__init__(self, name, bases, dict)


__MBean = MBeanClass('__MBean', (WasObject,))   

class MBean(__MBean):
	pass

