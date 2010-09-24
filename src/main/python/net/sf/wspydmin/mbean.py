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

import copy, re

from java.lang                 import Class as JavaClass

from net.sf.wspydmin           import Help
from net.sf.wspydmin.lang      import *
from net.sf.wspydmin.resources import Resource

class MBeanMethodInvoker:
    def __init__(self, mbeanId, methodName):
        self.mbeanId    = mbeanId
        self.methodName = methodName
    
    def __call__(self, *args, **kwargs):
        AdminControl.invoke(self.mbeanId, self.methodName, self.__parseargs__(args, kwargs))
    
    def __parseargs__(self, *args, **kwargs):
        return str(args)

class MBeanHelper(WasObjectHelper):
    
    def __helperinit__(self, klass):
        WasObjectHelper.__helperinit__(self, klass)
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
            return WasObjectHelper.__missedattr__(self, name)

class MBeanClass(WasObjectClass):
    __helper__       = MBeanHelper
    
    def __init__(self, name, bases = (), dict = {}):
        WasObjectClass.__init__(self, name, bases, dict)


MBean         = MBeanClass('MBean',         (WasObject,))
ResourceMBean = MBeanClass('ResourceMBean', (Resource,))
   
