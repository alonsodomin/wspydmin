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

__author__  = "A. Alonso Dominguez <alonsoft@users.sf.net>"
__status__  = "alpha"
__version__ = "0.2.0"

import copy, types, re, logging

from java.lang             import IllegalArgumentException
from com.ibm.ws.scripting  import ScriptingException
from net.sf.wspydmin       import *

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
        
        configidRE = re.compile(r'\"?(.+)\((.+)\|(.+)\#(.+)\)\"?')
        matches    = configidRE.findall(configid)
        if len(matches) > 0:
            self.name = matches[0][0]
            self.path = matches[0][1]
            self.file = matches[0][2]
            self.node = matches[0][3]
    
    def __str__(self):
        return ResourceConfigID.__STR_PATTERN % self.__dict__

class ResourceClassHelper(WasObjectClassHelper):
    __TEMPLATES         = {}
    __parent_attrname__ = 'parent'
    
    __inited            = 0
    
    ATTR_TYPE    = 'DEF_CFG_TYPE'
    ATTR_PATH    = 'DEF_CFG_PATH'
    ATTR_PARENT  = 'DEF_CFG_PARENT'
    ATTR_ATTRS   = 'DEF_CFG_ATTRS'
    ATTR_TMPL    = 'DEF_CFG_TMPL'
    
    def __helperinit__(self, klass):
        WasObjectClassHelper.__helperinit__(self, klass)
        
        if not hasattr(self, ResourceClassHelper.ATTR_TYPE):
            raise AbstractResourceError, klass.__name__
        
        self.__was_cfg_type__                   = getattr(self, ResourceClassHelper.ATTR_TYPE)
        self.__was_cfg_attrmap__                = {}
        self.__wasclass__.__was_cfg_attrtypes__ = {}
        
        if len(self.__wasclass__.__was_cfg_attrtypes__) == 0:
            attrdef = AdminConfig.attributes(self.__was_cfg_type__)
            if (attrdef is not None) and (attrdef != ''):
                for atype in attrdef.splitlines():
                    if (atype == ''): continue
                    attrdefRE = re.compile(r'([a-zA-Z0-9]+)\ (.+)')
                    matches   = attrdefRE.findall(atype)
                    if len(matches) > 0:
                        attrname  = matches[0][0]
                        attrvalue = matches[0][1]
                        try:
                            self.__wasclass__.__was_cfg_attrtypes__[attrname] = was_type(attrvalue)
                        except WasDataTypeError:
                            logging.error('Unknown data type: %s', attrvalue)
            logging.debug("Instance's attribute types for '%s' resource type defined.", 
                          klass.__name__)
        self.__inited = 1

    def __define_classtype__(self):
        try:
            was_define_class(self.__wasclass__, self.__was_cfg_type__)
        except WasDataTypeError:
            #WasObjectClassHelper.__define_classtype__(self)
            pass

    def __define_instance__(self):
        self.__hydrate()
        attrvalues = []
        if self.exists():
            logging.debug("Resource '%s' exists, loading attribute values from server...", self.__getconfigid__())
            attrvalues = AdminConfig.show(self.__getconfigid__().__str__()).splitlines()
        else:
            logging.debug("Resource doesn't exists, loading default attribute values from server...")
            attrvalues = AdminConfig.defaults(self.__was_cfg_type__).splitlines()[1:]
        for attr in attrvalues:
            if attr.startswith('[') and attr.endswith(']'):
                attr = attr[1:-1]               # Drop '[' and ']' from attribute string
            name  = attr.split(None, 1)[0]
            value = attr.split(None, 1)[1]
            if not self.__wasclass__.__was_cfg_attrtypes__.has_key(name):
                logging.warn("Ignoring attribute '%s' since no no type founded for it.", name) 
                continue
            #if not self.__was_cfg_attrmap__[attr] is None: continue
            logging.debug("Attribute '%s' will receive value '%s' from server.", name, value)
            self.__was_cfg_attrmap__[name] = self.__parseattr(name, value)

    def __getconfigid__(self):
        id = was_getconfigid(self.__was_cfg_path__)
        if (id is None) and hasattr(self, self.__parent_attrname__):
            parent = getattr(self, self.__parent_attrname__)
            id = parent.__getconfigid__()
        else:
            id = ResourceConfigID(id)
        return id

    def __getattr__(self, name):
        try:
            return WasObjectClassHelper.__getattr__(self, name)
        except AttributeError:
            if self.__was_cfg_attrmap__.has_key(name):
                val = self.__was_cfg_attrmap__[name]
                if val == '': val = None
                return val
            else:
                raise AttributeError, name

    def __setattr__(self, name, value):
        if self.__inited:
            if type("") == type(value):
                value = self.__parseattr(name, value)
            self.__was_cfg_attrmap__[name] = value
        else:
            self.__dict__[name] = value

    def __flatattr(self, name, value):
        if not self.__wasclass__.__was_cfg_attrtypes__.has_key(name):
            logging.warn("attribute '%s' can't be flattened since no type has been found", name)
            return value
        else:
            type = self.__wasclass__.__was_cfg_attrtypes__[name]
            return type.to_str(value)
    
    def __parseattr(self, name, value):
        if not self.__wasclass__.__was_cfg_attrtypes__.has_key(name):
            logging.warn("attribute '%s' can't be parsed since no type has been found" , name)
            return value
        else:
            type = self.__wasclass__.__was_cfg_attrtypes__[name]
            return type.from_str(value)

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
        return [ [label, self.__flatattr__(label, value) ] for label, value in self.__was_cfg_attrmap__.items() if not value is None ]
    
    def __dumpattrs__(self):
        str = ''
        if self.__inited:
            for name, value in self.__was_cfg_attrmap__.items():
                value = self.__flatattr(name, value)
                str = str + ("\t(%s) %s = %s\n" % (self.__was_cfg_attrtypes__[name], name, value))
        return str
    
    def __hydrate(self):
        if not hasattr(self, '__was_cfg_attrmap__'):
            raise IllegalStateException, "WAS resource unproperly initialized"
        
        logging.debug("hydrating WAS resource type: %s", self.__was_cfg_type__)
        # Collect public WAS attributes
        adict = copy.copy(self.__was_cfg_attrmap__)
        for k in adict.keys():
            if k.startswith('__'):
                del adict[k]
        
        # Resolve hydrated objet scope
        if not hasattr(self, ResourceClassHelper.ATTR_PARENT):
            if hasattr(self, self.__parent_attrname__):
                parent = getattr(self, self.__parent_attrname__)
                if not hasattr(parent, '__was_cfg_path__'):
                    raise IllegalStateException, "'%s' attribute must be a concrete and hydrated Resource instance" % self.__parent_attrname__
                self.__was_cfg_parent__ = parent.__was_cfg_path__
            else:
                self.__was_cfg_parent__ = ""
        else:
            if hasattr(self, self.__parent_attrname__):
                parent = getattr(self, self.__parent_attrname__)
                if hasattr(parent, '__was_cfg_path__'):
                    adict['parent'] = parent.__was_cfg_path__
            self.__was_cfg_parent__ = getattr(self, ResourceClassHelper.ATTR_PARENT) % adict
        adict['scope'] = self.__was_cfg_parent__
        
        # Hydrate object id
        self.__was_cfg_path__ = getattr(self, ResourceClassHelper.ATTR_PATH) % adict
        logging.debug("Resource hydrated with config path: %s", self.__was_cfg_path__)
        
        # Initialize template map for this resource type
        if not ResourceClassHelper.__TEMPLATES.has_key(self.__was_cfg_type__):
            ResourceClassHelper.__TEMPLATES[self.__was_cfg_type__] = {}
            for tplid in AdminConfig.listTemplates(self.__was_cfg_type__).splitlines():
                if tplid.startswith('"') and tplid.endswith('"'):
                    tplid = tplid[1:-1]
                ResourceClassHelper.__TEMPLATES[self.__was_cfg_type__][tplid.split('(')[0]] = tplid
        
        # Hydrate resource's template name
        template = None
        if hasattr(self, ResourceClassHelper.ATTR_TMPL):
            template = getattr(self, ResourceClassHelper.ATTR_TMPL) % adict
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
        if (template is not None) and ResourceClassHelper.__TEMPLATES[self.__was_cfg_type__].has_key(template):
            self.__was_cfg_template__ = ResourceClassHelper.__TEMPLATES[self.__was_cfg_type__][template]
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
        

class ResourceClass(WasObjectClass):
    __helper__ = ResourceClassHelper
    
    def __init__(self, name, bases = (), dict = {}):
        WasObjectClass.__init__(self, name, bases, dict)

Resource = ResourceClass('Resource', (WasObject,))

#class Resource2(Resource):
    
#    ATTR_PATH    = 'DEF_CFG_PATH'
#    ATTR_PARENT  = 'DEF_CFG_PARENT'
#    ATTR_ATTRS   = 'DEF_CFG_ATTRS'
#    ATTR_TMPL    = 'DEF_CFG_TMPL'
    
#    def __init__(self):
#        self.__was_cfg_attrmap = {}
#        if not hasattr(self, Resource.ATTR_PATH):
#            raise AbstractResourceError, self.__was_cfg_type__

        #self.__was_cfg_attrmap = copy.copy(getattr(self, Resource.ATTR_ATTRS))

def was_resource_pathid(pathid):
    pass