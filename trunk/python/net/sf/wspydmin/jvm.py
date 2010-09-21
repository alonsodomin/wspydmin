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

from net.sf.wspydmin            import AdminConfig, AdminControl
from net.sf.wspydmin.resources  import Resource
from net.sf.wspydmin.properties import Property

class JavaVirtualMachine(Resource):
	DEF_ID    = '/JavaVirtualMachine:/'
	DEF_ATTRS = {
			          'bootClasspath' : None,
			              'classpath' : None,
			              'debugArgs' : None,
			              'debugMode' : None,
			             'disableJIT' : None,
			    'genericJvmArguments' : None,
			         'hprofArguments' : None,
			        'initialHeapSize' : None,
			'internalClassAccessMode' : None,
			        'maximumHeapSize' : None,
			               'runHProf' : None,
			       'systemProperties' : None,
			       'verboseModeClass' : None,
	   'verboseModeGarbageCollection' : None,
	                 'verboseModeJNI' : None
	}
	
	def __init__(self, parent):
		Resource.__init__(self)
		self.parent     = parent
		self.properties = {}
	
	def __postinit__(self):
		Resource.__postinit__(self)
		self.genericJvmArguments = AdminConfig.showAttribute(self.__getconfigid__(), 'genericJvmArguments').split()
	
	def __create__(self, update):
		Resource.__create__(self, update)
		for name, prop in self.properties.items():
			prop.__create__(update)
	
	def __getconfigid__(self, id = None):
		return AdminConfig.list(self.__wastype__, self.parent.__getconfigid__()).splitlines()[0]
		
	def addGenericJvmArgument(self, genericJvmArgument):
		newJvmArgName   = genericJvmArgument.split('=')[0]
		newSettings     = [ setting for setting in self.genericJvmArguments if not setting.startswith(newJvmArgName) ] 
		newSettings.append(genericJvmArgument.replace("', '", " "))
		self.genericJvmArguments = str(newSettings)[2:-2]
		
	def addCustomProperty(self, name, value, required = None, description = None, validationExpression = None):
		p = Property(self)
		p.name                 = name
		p.value                = value
		p.description          = description
		p.validationExpression = validationExpression
		if required:
			p.required = 'true'
		self.properties[name] = p
