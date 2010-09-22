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

from java.lang                                     import IllegalArgumentException
from javax.management                              import MBeanException

from com.ibm.websphere.management.exception        import AdminException
from com.ibm.ws.scripting                          import ScriptingException

from net.sf.wspydmin                               import AdminConfig, AdminControl
from net.sf.wspydmin.admin                         import Cell
from net.sf.wspydmin.pool                          import ConnectionPool
from net.sf.wspydmin.resources                     import Resource
from net.sf.wspydmin.security                      import JAASAuthData
from net.sf.wspydmin.properties                    import J2EEPropertyHolderResource

class J2CResourceAdapter(Resource):
    DEF_ID    = '%(scope)sJ2CResourceAdapter:%(name)s/'
    DEF_ATTRS = {
        'name' : None
    }
    
    def __init__(self, name):
        Resource.__init__(self)
        self.name   = name
        self.parent = Cell()


class J2CRelationalResourceAdapter(J2CResourceAdapter):
	RESOURCE_ADAPTER_NAME = 'WebSphere Relational Resource Adapter'
	
	def __init__(self):
		J2CResourceAdapter.__init__(self, J2CRelationalResourceAdapter.RESOURCE_ADAPTER_NAME)

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

	def __init__(self, name):
		Resource.__init__(self)
		self.name   = name
		self.parent = J2CRelationalResourceAdapter()

	def __postinit__(self):
		Resource.__postinit__(self)
		if self.provider is None:
			self.provider = AdminConfig.getid(self.__scope__)

class JDBCProvider(Resource):
	DEF_ID    = '%(scope)sJDBCProvider:%(name)s/'
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

class DataSource(J2EEPropertyHolderResource):
	__parent_attrname__ = 'provider'
	
	DEF_ID    = '%(scope)sDataSource:%(name)s'
	DEF_ATTRS = {
                    'name' : None,
		   'authDataAlias' : None,
		    	'provider' : None,
			'providerType' : None,
	 'xaRecoveryAuthAlias' : None
	}
	
	AUTH_DATA_ALIAS = 'JDBC_%(userId)s_%(name)s'
	
	def __init__(self, provider):
		if provider is None:
			raise IllegalArgumentException, 'A provider must be given'
		
		J2EEPropertyHolderResource.__init__(self)
		self.__auth       = None
		self.__iscmp      = None
		self.__cmpcf      = None
        self.__pool       = ConnectionPool(self)
        self.provider     = provider
        self.providerType = provider.providerType
	
	def __create__(self, update):
		#1.- Configure Auth Data       
		if not self.__auth is None:                    
			self.__auth.__create__(update)
			self.authDataAlias = self.__auth.alias
			if (self.provider.xa and (self.xaRecoveryAlias is None)):
				# If provider is XA enabled, then configure XA recovery alias
				self.xaRecoveryAuthAlias = self.__auth.alias
		
		#2.- Configure JDBC Provider
		self.provider.__create__(update)
		
        #3.- Configure connection pool
        self.__pool.__create__(update)
        
		#4.- Configure Data source
        J2EEPropertyHolderResource.__create__(self, update)
        
		#5.- Configure CMP Factory if needed
        if not (self.__iscmp is None):
			self.__cmpcf.authDataAlias = self.authDataAlias
			self.__cmpcf.cmpDatasource = self.__getconfigid__()
			if self.__iscmp:
				if not self.__cmpcf.exists():
					self.__cmpcf.create()
				else:
					self.__cmpcf.update()
			else:
				self.__cmpcf.remove()

	def __loadattrs__(self):
		Resource.__loadattrs__(self)
		if not self.exists(): return
		if not self.authDataAlias is None:
			self.__auth = JAASAuthData(self.authDataAlias)

	def getAuthData(self):
		if (self.__auth is None) and (not self.authDataAlias is None):
			self.__auth = JAASAuthData(self.authDataAlias)
		if (self.__auth is None) and (not self.exists()): 
			return None
		return self.__auth
	
	def setAuthData(self, user, password, desc = None):
		alias = DataSource.AUTH_DATA_ALIAS % {
			'userId' : user, 
			'name'   : self.name
		}
		self.__auth             = JAASAuthData(alias)
		self.__auth.userId      = user
		self.__auth.password    = password
		self.__auth.description = desc
	
	def getConnectionPool(self):
		return self.__pool
	
	def isContainerManaged(self):
		return self.__iscmp
	
	def enableCMP(self):
		if self.__iscmp:
			raise Exception, 'CMP already enabled on DataSource "%s"' % self.__id__
		
		self.__iscmp = 1
		self.__cmpcf = CMPConnectorFactory("%s_CF" % self.name)
	
	def disableCMP(self):
		self.__iscmp = 0
		self.__cmpcf = None
	
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
