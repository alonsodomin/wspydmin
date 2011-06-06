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

from java.lang                              import IllegalArgumentException

from net.sf.wspydmin                        import AdminConfig
from net.sf.wspydmin.resources              import Resource
from net.sf.wspydmin.resources.topology     import ApplicationServer
from net.sf.wspydmin.resources.classloaders import ClassLoader

class Deployment(Resource):
	DEF_CFG_PATH    = '%(scope)sDeployment:%(appname)s/'
	DEF_CFG_ATTRS = {
		'appname' : None
	}
	
	def __init__(self, appname, parent = ApplicationServer()):
		Resource.__init__(self)
		self.appname          = appname
		self.parent           = parent
		self.__deployedObject = None
	
	def __loadattrs__(self):
		Resource.__loadattrs__(self)
		if not self.exists(): return
		deployedObj           = AdminConfig.showAttribute(self.__getconfigid__(), 'deployedObject')
		self.__deployedObject = DeployedObject(deployedObj, self)
	
	def __create__(self, update):
		Resource.__create__(self, update)
		self.__deployedObject.__create__(update)
	
	def __remove__(self, deep):
		self.__deployedObject.__remove__(deep)
		Resource.__remove__(self, deep)
	
	def getDeployedObject(self):
		return self.__deployedObject

class DeployedObject(Resource):
	DEF_CFG_ATTRS = {
		'wasClassLoaderPolicy' : 'SINGLE'
	}
	
	def __init__(self, deployedObjectId, parent):
		Resource.__init__(self)
		self.parent        = parent
		self.__doi         = deployedObjectId
		self.__classloader = None

	def __create__(self, update):
		Resource.__create__(self, update)
		self.__classloader.__create__(update)
	
	def __getconfigid__(self):
		return self.__doi
	
	def __loadattrs__(self):
		Resource.__loadattrs__(self)
		if not self.exists(): return
		classloader        = AdminConfig.showAttribute(self.__getconfigid__(), 'classloader')
		self.__classloader = ClassLoader()

	def getClassLoader(self):
		return self.__classloader



def setDeploymentClassLoader(appname, mode='PARENT_LAST', policy='SINGLE', server = ApplicationServer()):
	if (mode != 'PARENT_LAST') and (mode != 'PARENT_FIRST'):
		raise IllealArgumentException('Illegal class loader mode: %s' % mode)
	logging.info("Setting '%s' application classloader to mode '%s' and warClassLoaderPolicy '%s'" % (appname, mode, policy))
    #dep = AdminConfig.getid('/Deployment:%s/' % appname)
    #depObject = AdminConfig.showAttribute(dep, 'deployedObject')
    #classldr = AdminConfig.showAttribute(depObject, 'classloader')
    #AdminConfig.modify(classldr, [['mode', mode]])
    #AdminConfig.modify(depObject, [['warClassLoaderPolicy', policy]])
	deployment  = Deployment(appname, server)
	if not deployment.exists():
		raise IllegalArgumentException('Application deployment "%s" not found!' % appname)

	deployedObj = deployedObj.getDeployedObject()
	deployedObj.wasClassLoaderPolicy = policy
	if mode == 'PARENT_LAST':
		deployedObj.getClassLoader().setParentLast()
	else:
		deployedObj.getClassLoader().setParentFirst()
	deployment.update()