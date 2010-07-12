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

import sys, traceback, copy

from java.lang                                     import Exception
from javax.management                              import MBeanException

from com.ibm.websphere.management.exception        import AdminException
from com.ibm.ws.scripting                          import ScriptingException

from net.sf.wspydmin                               import AdminConfig, AdminControl
from net.sf.wspydmin.pool                          import ConnectionPool
from net.sf.wspydmin.resources                     import Resource
from net.sf.wspydmin.security                      import JAASAuthData
from net.sf.wspydmin.properties                    import J2EEPropertySetResource

class CMPConnectorFactory(Resource):
	DEF_SCOPE = '/Cell:%s/J2CResourceAdapter:WebSphere Relational Resource Adapter/' % AdminControl.getCell()
	DEF_ID    = '%(scope)sCMPConnectorFactory:%(name)s/'
	DEF_TPL   = None
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

	def __init__(self, name):
		Resource.__init__(self)
		self.name = name

	def __postinit__(self):
		Resource.__postinit__(self)
		if self.provider is None:
			self.provider = AdminConfig.getid(self.__scope__)

class JDBCProvider(Resource):
	DEF_SCOPE = '/Cell:%s' % AdminControl.getCell()
	DEF_ID    = '%(scope)s/JDBCProvider:%(name)s/'
	DEF_TPL   = None
	DEF_ATTRS = {
						   'name' : None,
                   'providerType' : None,
        'implementationClassName' : None,
                      'classpath' : None,
					 'nativepath' : None,
                             'xa' : 'false',
                    'description' : None
	}
	
	def __init__(self, name):
		Resource.__init__(self)
		self.name = name

class DataSource(J2EEPropertySetResource):
	
	AUTH_DATA_ALIAS = 'JDBC_%(userId)s_%(name)s'
	
	def __init__(self):
		J2EEPropertySetResource.__init__(self)
		self.__auth__     = None
		self.__cmp__      = None
		self.__cmpcf__    = None		
		self.__provider__ = None
	
	def __create__(self, update):
		#1.- Configure Auth Data       
		if not self.__auth__ is None:                    
			alias = DataSource.AUTH_DATA_ALIAS % {
				'userId' : self.__auth__.userId, 
				'name'   : self.name
			}
			self.__auth__.alias = alias
			self.__auth__.__create__(update)
			self.authDataAlias = self.__auth__.alias
			if self.__provider__.xa == 'true':
				self.xaRecoveryAuthAlias = self.__auth__.alias
		
		#2.- Configure JDBC Provider
		self.__provider__.__create__(update)
		self.provider     = self.__provider__.__getconfigid__()
		self.providerType = self.__provider__.providerType
		self.__scope__    = self.__provider__.id
		
		#3.- Configure Data source
		J2EEPropertySetResource.__create__(self, update)
		
		#4.- Configure CMP Factory if needed
		if not (self.__cmp__ is None):
			self.__cmpcf__.authDataAlias = alias
			self.__cmpcf__.cmpDatasource = self.__getconfigid__()
			if self.__cmp__:
				self.__cmpcf__.create()
			else:
				self.__cmpcf__.remove()
	
	def __setattr__(self, name, value):
		J2EEPropertySetResource.__setstdattr__(self, name, value)
		if (name == '__cmp__'):
			self.__cmp__   = (value == 'true')
			self.__cmpcf__ = CMPConnectorFactory("%s_CF" % self.name)				

	def getAuthData(self):
		if not self.exists(): return None
		if self.__auth__ is None:
			self.__auth__ = JAASAuthData()
			self.__auth__.alias = self.authDataAlias
		return self.__auth__
	
	def setAuthData(self, user, password, desc = None):
		self.__auth__             = JAASAuthData()
		self.__auth__.userId      = user
		self.__auth__.password    = password
		self.__auth__.description = desc
	
	def getConnectionPool(self):
		return ConnectionPool(self)
	
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
