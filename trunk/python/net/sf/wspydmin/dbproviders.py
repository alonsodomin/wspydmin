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

from net.sf.wspydmin.resources import Resource
from net.sf.wspydmin.jdbc      import JDBCProvider, DataSource

class OracleJDBCProvider(JDBCProvider):
	DEF_TPL = 'Oracle JDBC Driver'

	def __init__(self):
		JDBCProvider.__init__(self, OracleJDBCProvider.DEF_TPL)

	def __loaddefaults__(self):
		self.providerType = 'Oracle JDBC Driver'
		self.implementationClassName = 'oracle.jdbc.pool.OracleConnectionPoolDataSource'
		self.classpath = '${ORACLE_JDBC_DRIVER_PATH}/ojdbc14.jar'
		self.description = 'Oracle JDBC Provider'
	
	def __create__(self, update):
		JDBCProvider.__create__(self, update)
		junk = DataSource()
		junk.name = 'Oracle JDBC Driver DataSource'
		junk.remove()

class OracleXaJDBCProvider(JDBCProvider):
	DEF_TPL = 'Oracle JDBC Driver (XA)'

	def __init__(self):
		JDBCProvider.__init__(self, OracleXaJDBCProvider.DEF_TPL)

	def __loaddefaults__(self):
		self.providerType = 'Oracle JDBC Driver (XA)'
		self.implementationClassName = 'oracle.jdbc.xa.client.OracleXADataSource'
		self.classpath = '${ORACLE_JDBC_DRIVER_PATH}/ojdbc14.jar'
		self.description = 'Oracle JDBC Driver (XA)'
		self.xa = 'true'
	
	def __create__(self, update):
		JDBCProvider.__create__(self, update)
		junk = DataSource()
		junk.name = 'Oracle JDBC Driver XA DataSource'
		junk.remove()

class DB2UDBJDBCProvider(JDBCProvider):
	
	def __init__(self):
		JDBCProvider.__init__(self, 'DB2 UDB for iSeries JDBC Provider')

	def __loaddefaults__(self):
		self.providerType = 'DB2 UDB for iSeries (Toolbox)'
		self.implementationClassName = 'com.ibm.as400.access.AS400JDBCConnectionPoolDataSource'
		self.classpath = '${OS400_TOOLBOX_JDBC_DRIVER_PATH}/jt400.jar'
		self.description = 'IBM Toolbox for Java JDBC Driver for remote DB2 connections on iSeries. This driver is recommended over the IBM Developer Kit for Java JDBC Driver for access to remote DB2 UDB for iSeries. The jar file for this driver is /QIBM/ProdData/Http/Public/jt400/lib/jt400.jar'

class IngressJDBCProvider(JDBCProvider):
	
	def __init__(self):
		JDBCProvider.__init__(self, 'Ingress JDBC Provider')

	def __loaddefaults__(self):
		#self.providerType = 'User-defined JDBC Provider'
		self.implementationClassName = 'com.ingres.jdbc.IngresCPDataSource'
		self.classpath = '${INGRES_JDBC_DRIVER_PATH}/iijdbc.jar'
		self.description = 'Custom JDBC2.0-compliant Provider configuration'
		self.xa = 'false'

class SybaseJDBCProvider(JDBCProvider):
	
	def __init__(self):
		JDBCProvider.__init__(self, 'Sybase JDBC 3 Driver')
	
	def __loaddefaults__(self):
		self.providerType = 'Sybase JDBC 3 Driver'
		self.implementationClassName = 'com.sybase.jdbc3.jdbc.SybConnectionPoolDataSource'
		self.classpath = '${SYBASE_JDBC_DRIVER_PATH}/jconn3.jar'
		self.description = 'Sybase JDBC 3 Driver'
		self.xa = 'false'

class OracleDataSource(DataSource):
	DEF_TPL   = 'Oracle JDBC Driver DataSource'
	DEF_PROPS = {
		                        'driverType' : 'thin',
		                       'description' : None,
		                      'databaseName' : None,
		                    'datasourceName' : None,
		                        'serverName' : None,
		                        'portNumber' : 1521,
		                      'TNSEntryName' : None,
		                               'url' : None,
		                      'loginTimeout' : None,
		                   'networkProtocol' : None,
		'enableMultithreadedAccessDetection' : 'false',
		                  'reauthentication' : 'false',
		           'jmsOnePhaseOptimization' : 'false',
		                  'preTestSQLString' : 'SELECT 1 FROM DUAL',
		             'validateNewConnection' : 'false',
		'validateNewConnectionRetryInterval' : 3,
		                 'dbFailOverEnabled' : None,
		       'connRetriesDuringDBFailover' : None,
		 'connRetryIntervalDuringDBFailover' : None,
		            'oracleLogFileSizeLimit' : 0,
		                'oracleLogFileCount' : 1,
		                 'oracleLogFileName' : None,
		               'oracleLogTraceLevel' : 'INFO',
		             'oracle9iLogTraceLevel' : 2,
		                   'oracleLogFormat' : 'SimpleFormat',
		              'oracleLogPackageName' : 'oracle.jdbc.driver'
	}
	
	def __init__(self, name, provider = OracleJDBCProvider()):
		DataSource.__init__(self, provider)
		self.name                      = name
		self.dataSourceHelperClassName = 'com.ibm.websphere.rsadapter.OracleDataStoreHelper'		

class OracleXaDataSource(OracleDataSource):
	DEF_TPL   = 'Oracle JDBC Driver XA DataSource'
	
	def __init__(self, name):
		OracleDataSource.__init__(self, name, OracleXaJDBCProvider())

class Oracle10gDataSource(OracleDataSource):
	def __init__(self, name):
		OracleDataSource.__init__(self, name)
		self.datasourceHelperClassname = 'com.ibm.websphere.rsadapter.Oracle10gDataStoreHelper'

class Oracle10gXaDataSource(OracleXaDataSource):
	def __init__(self, name):
		OracleXaDataSource.__init__(self, name)
		self.datasourceHelperClassname = 'com.ibm.websphere.rsadapter.Oracle10gDataStoreHelper'

class IngressDataSource(DataSource):
	DEF_PROPS = {
		        'user' : None,
		    'password' : None,
		  'serverName' : None,
		    'portName' : None,
		'databaseName' : None
	}
	
	def __init__(self, name):
		DataSource.__init__(self)
		self.name         = name
		self.__provider__ = IngressJDBCProvider()

class SybaseDataSource(DataSource):
	DEF_PROPS = {
		'databaseName' : None,
		  'serverName' : None,
		  'portNumber' : None
	}
	
	def __init__(self, name):
		DataSource.__init__(self)
		self.__provider__              = SybaseJDBCProvider()
		self.name                      = name
		self.datasourceHelperClassname = 'com.ibm.websphere.rsadapter.SybaseDataStoreHelper'
