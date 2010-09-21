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

import sys, traceback, copy

from java.lang                                     import Exception
from javax.management                              import MBeanException

from com.ibm.websphere.management.exception        import AdminException
from com.ibm.ws.scripting                          import ScriptingException

from net.sf.wspydmin                               import AdminConfig, AdminControl
from net.sf.wspydmin.admin                         import Cell
from net.sf.wspydmin.adapters                      import J2CResourceAdapter  
from net.sf.wspydmin.pool                          import ConnectionPool
from net.sf.wspydmin.resources                     import Resource
from net.sf.wspydmin.security                      import JAASAuthData
from net.sf.wspydmin.properties                    import J2EEPropertySetResource

class CMPConnectorFactory(Resource):
	DEF_ID    = '%(scope)sCMPConnectorFactory:%(name)s/'
	DEF_ATTRS = {
                               'name' : None,
                      'authDataAlias' : None,
            'authMechanismPreference' : 'BASIC_PASSWORD',
                      'cmpDatasource' : None,
                   'customProperties' : None,
            'diagnoseConnectionUsage' : 'false',
       'logMissingTransactionContext' : 'true',
                'manageCachedHandles' : 'false',
                            'mapping' : None,
                        'propertySet' : None,
                           'provider' : None
	}

	J2C_RESOURCE_ADAPTER_NAME = 'WebSphere Relational Resource Adapter'

	def __init__(self, name):
		Resource.__init__(self)
		self.name   = name
		self.parent = J2CResourceAdapter(CMPConnectorFactory.J2C_RESOURCE_ADAPTER_NAME)

	def __postinit__(self):
		Resource.__postinit__(self)
		if self.provider is None:
			self.provider = AdminConfig.getid(self.__scope__)

class JDBCProvider(Resource):
	DEF_ID    = '%(scope)s/JDBCProvider:%(name)s/'
	DEF_ATTRS = {
						   'name' : None,
                   'providerType' : None,
        'implementationClassName' : None,
                      'classpath' : None,
					 'nativepath' : None,
                             'xa' : 'false',
                    'description' : None
	}
	
	def __init__(self, name, parent = Cell()):
		Resource.__init__(self)
		self.name   = name
		self.parent = parent

class DataSource(J2EEPropertySetResource):
	DEF_ID    = '%(scope)sDataSource:%(name)s'
	DEF_ATTRS = {
		   'authDataAlias' : None,
		    	'provider' : None,
			'providerType' : None,
	 'xaRecoveryAuthAlias' : None
	}
	
	AUTH_DATA_ALIAS = 'JDBC_%(userId)s_%(name)s'
	
	def __init__(self, provider):
		J2EEPropertySetResource.__init__(self)
		self.__auth__     = None
		self.__iscmp__    = None
		self.__cmpcf__    = None
		
		self.parent       = provider
		self.provider     = self.parent.__getconfigid__()
		self.providerType = self.parent.providerType
	
	def __create__(self, update):
		#1.- Configure Auth Data       
		if not self.__auth__ is None:                    
			self.__auth__.__create__(update)
			self.authDataAlias = self.__auth__.alias
			if (self.parent.xa and (self.xaRecoveryAlias is None)):
				# If provider is XA enabled, then configure XA recovery alias
				self.xaRecoveryAuthAlias = self.__auth__.alias
		
		#2.- Configure JDBC Provider
		self.parent.__create__(update)
		
		#3.- Configure Data source
		J2EEPropertySetResource.__create__(self, update)
		
		#4.- Configure CMP Factory if needed
		if not (self.__iscmp__ is None):
			self.__cmpcf__.authDataAlias = alias
			self.__cmpcf__.cmpDatasource = self.__getconfigid__()
			if self.__iscmp__:
				if not self.__cmpcf__.exists():
					self.__cmpcf__.create()
				else:
					self.__cmpcf__.update()
			else:
				self.__cmpcf__.remove()

	def getAuthData(self):
		if (self.__auth__ is None) and (not self.authDataAlias is None):
			self.__auth__ = JAASAuthData(self.authDataAlias)
		if (self.__auth__ is None) and (not self.exists()): 
			return None
		return self.__auth__
	
	def setAuthData(self, user, password, desc = None):
		alias = DataSource.AUTH_DATA_ALIAS % {
			'userId' : user, 
			'name'   : self.name
		}
		
		self.__auth__             = JAASAuthData(alias)
		self.__auth__.userId      = user
		self.__auth__.password    = password
		self.__auth__.description = desc
	
	def getConnectionPool(self):
		return ConnectionPool(self)
	
	def isContainerManaged(self):
		return self.__iscmp__
	
	def enableCMP(self):
		if self.__iscmp__:
			raise Exception, 'CMP already enabled on DataSource "%s"' % self.__id__
		
		self.__iscmp__ = 1
		self.__cmpcf__ = CMPConnectorFactory("%s_CF" % self.name)
	
	def disableCMP(self):
		self.__iscmp__ = 0
		self.__cmpcf__ = None
	
	def testConnection(self):
		return AdminControl.testConnection(self.__getconfigid__())
	
def testDataSource(ds):
	print "Testing Datasource '%s'..." % ds.name
	print 'result is: %s ' % ds.testConnection()

def testAllDataSourcesInCurrentCell():
	print "Testing all DataSource..."
	for dsName in map(lambda x: x.split('(')[0], AdminConfig.list('DataSource').splitlines()):
		try:
			ds = DataSource()
			ds.name = dsName
			testDataSource(ds)
		except:
			print >> sys.stderr, "ERROR: datasource '%s' is not working properly. Exception is: %s" % (dsName, sys.exc_info())
