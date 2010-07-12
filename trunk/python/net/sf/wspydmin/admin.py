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

from java.lang                   import IllegalArgumentException, IllegalStateException

from net.sf.wspydmin             import AdminConfig, AdminControl, AdminTask
from net.sf.wspydmin.utils       import *
from net.sf.wspydmin.resources   import Resource, MBean
from net.sf.wspydmin.listener    import MessageListenerService
from net.sf.wspydmin.orb         import ObjectRequestBroker
from net.sf.wspydmin.web         import WebContainer
from net.sf.wspydmin.transaction import TransactionService
from net.sf.wspydmin.vars        import VariableSubstitutionEntry
from net.sf.wspydmin.jvm         import JavaVirtualMachine

class Cell:
	DEF_ID = '/Cell:%s/'
	
	def __init__(self, name = AdminControl.getCell()):
		self.name   = name
		self.__id__ = Cell.DEF_ID % name

	def __getconfigid__(self):
		return AdminConfig.getid(self.__id__)

	def __getserverids__(self):
		return AdminConfig.list('Server', self.__id__).splitlines()

	def getName(self):
		return self.name
	
	def getServers(self):
		return map(Server, self.__getserverids__())
    
	def getWebServers(self):
		return map(Server, filter(isWebServer, self.__getserverids__()))
    
	def getAdminServers(self):
		return map(Server, filter(isAdminServer, self.__getserverids__()))
    
	def getManagedServers(self):        
		return map(Server, filter(isManagedServer, self.__getserverids__()))
    
	def getNodeAgentServers(self):
		return map(NodeAgent, filter(isNodeAgentServer, AdminConfig.list('Server').splitlines()))

	def isClustered(self):
		return len(filter(isServerClustered, self.getAdminServers()))
    
	def getAdminhostPort(self): 
		srv  = map(getServerName, self.getAdminServers())[0]
		adm  = filter(isAdminHost, AdminTask.listServerPorts(srv).splitlines())
		port = map(getPort, adm)[0]
        
		print 'Admin host port (port range start) is %i' % port 
		return port
    
	def getCluster(self, name = None):
		#TODO: return an array or map containing all clusters in this cell
		#      if given name is None, otherwise return the Cluster with
		#      given name.
		if (not self.isClustered()):
			raise IllegalStateException, "No cluster found in cell '%s'" % self.name
		else:
			return Cluster(name, self)
        
	def containsWebServers(self):
		if ( len(self.getWebServers())> 0):
			return 1
		else:
			return 0

	def getAppName(self):
		cellName = self.name
		envName  = self.getEnvType()
		return cellName.split('_'+envName)[0]

	def getEnvType(self):
		return self.getName().split('_')[1].split('_CE')[0]    
    
	def getDefaultTrustStoreName(self):
		if (self.isClustered()):
			return 'CellDefaultTrustStore'
		else:
			return 'NodeDefaultTrustStore'

	def getVirtualHost(self, virtualHostName):
		return VirtualHost(virtualHostName)

	def getSharedLibraryIds(self):
		return AdminConfig.list('Library', self.__id__).splitlines()
    
	def getSharedLibraryReferenceIds(self):
		return AdminConfig.list('LibraryRef', self.__id__).splitlines()

class VirtualHost(Resource):
	DEF_SCOPE = None
	DEF_ID    = '/VirtualHost:/'
	DEF_ATTRS = {}
	
	def __init__(self, virtualHostName):
		self.virtualHostName = virtualHostName
		
	def __getconfigid__(self, id = None):
		id = None
		virtualHosts = AdminConfig.list('VirtualHost').splitlines()
		for virtualHostId in virtualHosts:
			if ( virtualHostId.find(self.virtualHostName) != -1 ):
				id = virtualHostId
				break
		return id

	def addHostAlias(self, hostName, portNumber):
		AdminConfig.create('HostAlias', self.id, [['hostname',hostName],['port',`portNumber`]])
	
	def addGenericHostAliasOnWC_defaulthostPort(self):
		self.addHostAlias('*', getBasePort() + 50)
    
	def addGenericHostAliasOnWC_adminhost_securePort(self):
		cell = Cell()
		increment = 3
		if (cell.isClustered()):
			increment = 1
		self.addHostAlias('*', getBasePort()+increment)
	
	def getHostAliasIds(self):
		return AdminConfig.list('HostAlias', self.id)
	
	def removeHostAliases(self):
		for hostAliasId in self.getHostAliasIds():
			AdminConfig.remove(hostAliasId)
	
class Cluster(MBean):
	def __init__(self, name, parent = None):
		self.name   = name
		self.parent = parent
		
		self.id = None
		clusters = AdminConfig.list('ServerCluster').splitlines()
		for clusterId in clusters:
			clusterName = getClusterName(clusterId)
			if clusterName == self.name:
				self.id = clusterId
		
		if (self.id is None):
			raise IllegalArgumentException, "No cluster '%s' was found in cell '%s'" % (self.name, AdminControl.getCell())
	
	def __getmbeanid__(self):
		return AdminControl.queryNames('cell=%s,type=Cluster,name=%s,*' % (AdminControl.getCell(), self.name))

class Server(MBean):
	DEF_SCOPE = '/Node:%(nodeName)s/'
	DEF_ID    = '%(scope)sServer:%(name)s/'
	DEF_TPL   = None
	DEF_ATTRS = {}
	
	def __init__(self, serverId):
		MBean.__init__(self)
		self.serverId   = serverId
		self.nodeName   = serverId.split('nodes/')[1].split('/servers')[0]
		self.serverName = getServerName(serverId)		
	
	def __hydrate__(self):
		self.__scope__ = Server.DEF_SCOPE % { 'nodeName' : self.nodeName }
		self.__id__    = Server.DEF_ID % { 'scope' : self.__scope__, 'name' : self.serverName }
	
	def addApplicationFirstClassLoader(self):
		classLoaderIds = AdminConfig.list('Classloader',self.__getconfigid__()).splitlines()
		print '%i classloader(s) is defined on server %s' % (len(classLoaderIds), self.serverName)
		if(len(classLoaderIds)>2):
			raise IllegalStateException, 'There is more than two classloader on server %s. another classloader cannot be added for safety reasons'  % (self.id)
		if(len(classLoaderIds)==2):
			raise IllegalStateException, 'CSE WAS Automation FW does not support several classloader for server.. please contact architecture team'
		if(len(classLoaderIds)==1):
			classLoaderMode = AdminConfig.showAttribute(classLoaderIds[0],'mode')
			print 'server %s already has one %s classloader defined' % (self.serverName, classLoaderMode)
			if (classLoaderMode=='PARENT_LAST'):
				print 'a PARENT_LAST ClassLoader already exist on this server.. there is no need to create another one'
			if (classLoaderMode=='PARENT_FIRST'):
				raise IllegalStateException, 'CSE WAS Automation FW does not support several classloader for server.. please contact architecture team'     		
		if(len(classLoaderIds)==0):
			#TODO refactoring on class loader class to have proper scope SERVER other than application
			print 'about to create a new classloader PARENT_LAST on server %s' % (self.__getconfigid__())
			AdminConfig.create('Classloader',self.getApplicationServerId(),[['mode','PARENT_LAST']])
	
	def getApplicationServerId(self):
		return AdminConfig.list('ApplicationServer', self.__getconfigid__()).splitlines()[0]
	
	def getJavaVirtualMachine(self):
		return JavaVirtualMachine(self)
	
	def getMessageListenerService(self):
		return MessageListenerService(self)
	
	def getProfileRootPath(self):
		vAdm = VariableSubstitutionEntry()
		return vAdm.getVariableValue('USER_INSTALL_ROOT' , getNodeId(self.__getconfigid__()) )
	
	def getObjectRequestBroker(self):
		return ObjectRequestBroker(self)
	
	def getThreadPool(self, name):
		return ThreadPool(name, self)
	
	def getThreadPools(self):
		tps = {}
		def getTpName(x): return x.split('(')[0]
		for name in map(getTpName, AdminConfig.list('ThreadPool', AdminConfig.getid(self.__id__))):
			tps[name] = self.getThreadPool(name)
            
		return tps

	def getTransactionService(self):
		return TransactionService(self)
	
	def getTunningParams(self):
		return TunningParams(self)
	
	def getWebContainer(self):
		return WebContainer(self)
	
	def isAdminServer(self):
		return isAdminServer(self.serverId)
	
	def isManagedServer(self):
		return isManagedServer(self.serverId)
	
	def isWebServer(self):
		return isWebServer(self.serverId)
	
	def removeAnyClassLoader(self):
		pass

class NodeAgent(Server):
	def __init__(self, serverId):
		Server.__init__(self, serverId)
		#self.nodeName = getNodeName(serverId)

	def __getmbeanid__(self):
		queryResult = AdminControl.queryNames('cell=%s,processType=NodeAgent,process=nodeagent,node=%s,*' % (AdminControl.getCell(), selg.nodeName))
		if (queryResult != ''):
			return queryResult.splitlines()[0]
		else:
			raise Exception, 'JMX MBEAN UNAVAILABLE'

class Node(Server):

	def __init__(self, serverId = AdminControl.getNode()):
		Server.__init__(self, serverId)

def getBasePort(cell = Cell()):
	port = cell.getAdminhostPort()
	if cell.isClustered():
		return port
	else:
		return port - 1

def changeSIBandSIPPortsInMServers(cell = Cell()): 
	#offset used to start the port must be hardcoded here 
	startingPort = getBasePort(cell) + 90 
	endingPort   = startingPort      + 7 
	print 'SIB and SIP ports (6 ports) will be changed incrementally, starting from port %i and ending at port %i' %(startingPort, endingPort)

	endPoints = {
               'SIB_ENDPOINT_ADDRESS' : `startingPort+0`,
        'SIB_ENDPOINT_SECURE_ADDRESS' : `startingPort+1`, 
            'SIB_MQ_ENDPOINT_ADDRESS' : `startingPort+2`, 
     'SIB_MQ_ENDPOINT_SECURE_ADDRESS' : `startingPort+3`, 
                    'SIP_DEFAULTHOST' : `startingPort+4`, 
             'SIP_DEFAULTHOST_SECURE' : `startingPort+5` 
	}
    
	changePorts(cell.getManagedServers(), endPoints)

def changeWCDefaultPortsInMServers(cell = Cell()): 
	#offset used to start the port must be hardcoded here 
	startingPort = getBasePort(cell) + 50 
	endingPort   = startingPort      + 2 
	print 'WCDefault ports (2 ports) will be changed incrementally, starting from port %i and ending at port %i' %(startingPort, endingPort)

	endPoints = {
               'WC_defaulthost' : `startingPort+0`,
        'WC_defaulthost_secure' : `startingPort+1`
	}

	changePorts(cell.getManagedServers(), endPoints)


def changeORBListenerPortInMServers(cell = Cell()): 
	#offset used to start the port must be hardcoded here 
	startingPort = getBasePort(cell) + 20 
	endingPort   = startingPort      + 1 
	print 'ORB Listener Port (1 ports) will be changed incrementally, starting from port %i and ending at port %i' %(startingPort, endingPort)

	endPoints = {'ORB_LISTENER_ADDRESS' : `startingPort`}

	changePorts(cell.getManagedServers(), endPoints)
