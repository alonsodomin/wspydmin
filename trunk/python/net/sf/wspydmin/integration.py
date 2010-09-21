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

from net.sf.wspydmin           import AdminConfig, AdminControl, AdminTask
from net.sf.wspydmin.resources import Resource
from net.sf.wspydmin.jdbc      import DataSource
from net.sf.wspydmin.admin     import Cell, Node, Server, Cluster
from net.sf.wspydmin.utils     import getServerName, getNodeName

class SIResource(Resource):
	
	def __getconfigid__(self):
		raise NotImplementedError, "ERROR: %s.__getconfigid__() not implemented" % self.__wastype__
	
	def __collectattrs__(self):
		str = ''
		for label, value in self.__wasattrmap__.items():
			if not value is None:
				str = '%s -%s %s' % (str, label, value)
		return str

class SIBus(SIResource):
	DEF_ID    = '/SIBus:%(bus)s/'
	DEF_ATTRS = {
                        'bus' : None,                      
                'busSecurity' : None, 
                'description' : None,
        'mediationsAuthAlias' : None,
                   'protocol' : None,
            'discardOnDelete' : None
	}
	
	def __init__(self, name, parent = Cell()):
		SIResource.__init__(self)
		self.bus            = name
		self.parent         = parent
		self.__busmembers__ = []
		
	def __create__(self, update):    
		params = self.__collectattrs__()
		print "Configuring SIBus with attributes %s" % params
		if update:
			AdminTask.modifySIBus(params)
		else:
			AdminTask.createSIBus(params)
        
		for busMember in self.__busmembers__:
			busMember.__create__(update)
	
	def addApplicationServerAsBusMember(self, nodeName, serverName):
		member = SIBusMember( self.bus )
		member.node   = nodeName
		member.server = serverName
		self.__busmembers__.append( member )
	
	def addSIBusMember(self, siBusMember):
		self.__busmembers__.append(siBusMember)
	
	def addClusterServerAsBusMember(self, clusterName, storeType='file'):
		member = SIBusMember( self.bus )
		member.cluster = clusterName
		
		if (storeType=='file'):
			member.fileStore               = ''
			member.logDirectory            = 'CL_busMember_logDir_' + clusterName
			member.permanentStoreDirectory = 'CL_busMember_permStoreDir_' + clusterName
			member.temporaryStoreDirectory = 'CL_busMember_tempStoreDir_' + clusterName
		else:
			raise NotImplementedException('please implement the Datastore feature for cluster bus members')
        
		self.__busmembers__.append( member )
	
	def addServerAsBusMember(self, serverName):
		member = SIBusMember( self.bus )
		member.server = serverName
		self.__busmembers__.append( member )
    
	def addWmqServerAsBusMember(self, wmqServerName):
		member = SIBusMember( self.bus )
		member.wmqServer = wmqServerName
		self.__busmembers__.append( member )
	
	def remove(self):
		for busMemberId in AdminConfig.showAttribute(self.__getconfigid__(), 'busMembers')[1:-1].splitlines():
			node   = AdminConfig.showAttribute(busMemberId, 'node')
			server = AdminConfig.showAttribute(busMemberId, 'server')
			# Remove associated DataSource 
			dsName = '_%s.%s-%s' % (node, server, self.bus)
			ds = DataSource(dsName)
			ds.remove()
		
		Resource.remove(self)
	
	def removeAll(self):
		for sibName in map(lambda x: x.split('(')[0], AdminConfig.getid('/SIBus:/').splitlines()):
			SIBus(sibName).remove()

class SIBusMember(SIResource):
	DEF_ID    = '/SIBusMember:%(bus)s/'
	DEF_ATTRS = {
                                 'bus' : None,
                             'channel' : None,
                   'securityAuthAlias' : None,
                      'transportChain' : None,
                        'trustUserIds' : None,
                             'cluster' : None,
                                'node' : None,
                              'server' : None,
                           'wmqServer' : None,
                         'description' : None,
                                'host' : None,
								'port' : None,
                      'transportChain' : None,
                        'trustUserIds' : None,
                           'fileStore' : None,
                             'logSize' : None,
                        'logDirectory' : None,
               'minPermanentStoreSize' : None,
               'minTemporaryStoreSize' : None,
               'maxPermanentStoreSize' : None,
               'maxTemporaryStoreSize' : None,
         'unlimitedPermanentStoreSize' : None,
         'unlimitedTemporaryStoreSize' : None,
             'permanentStoreDirectory' : None,
             'temporaryStoreDirectory' : None,
                           'dataStore' : None,
             'createDefaultDatasource' : None,
                        'createTables' : None,
                  'authAliasauthalias' : None,
                          'schemaName' : None,
                  'datasourceJndiName' : None
	}
	
	def __init__(self, busName, parent = Cell()):
		SIResource.__init__(self)
		self.bus    = busName
		self.parent = parent
		
	def __create__(self, update):
		params = self.__collectattrs__()
		print "Configuring SIBusMember with attributes %s" % params
		if update:
			AdminTask.modifySIBusMember(params)
		else:
			AdminTask.addSIBusMember(params)
	
	def remove(self):
		print >> sys.stderr, "WARN: SIBusMember.remove() not implemented. User SIBus.remove() instead."

	def removeAll(self):
		print >> sys.stderr, "WARN: SIBusMember.removeAll() not implemented. User SIBus.removeAll() instead."

class SIBJMSConnectionFactory(SIResource):
	DEF_ID    = '/SIBJMSConnectionFactory:%(name)s/'
	DEF_ATTRS = {
                                  'name' : None,
                              'jndiName' : None,
                               'busName' : None,
                                  'type' : None,
                         'authDataAlias' : None,
                   'xaRecoveryAuthAlias' : None,
                              'category' : None,
                           'description' : None,
          'logMissingTransactionContext' : None,
                   'manageCachedHandles' : None,
                              'clientID' : None,
                              'userName' : None,
                              'password' : None,
               'durableSubscriptionHome' : None,
                  'nonPersistentMapping' : None,
                     'persistentMapping' : None,
               'durableSubscriptionHome' : None,
                             'readAhead' : None,
                                'target' : None,
                            'targetType' : None,
                    'targetSignificance' : None,
                  'targetTransportChain' : None,
                     'providerEndPoints' : None,
                   'connectionProximity' : None,
                   'tempQueueNamePrefix' : None,
                   'tempTopicNamePrefix' : None,
                'shareDataSourceWithCMP' : None,
             'shareDurableSubscriptions' : None                 
	}
	
	QUEUE_CONNECTION_FACTORY = 'queue'
	TOPIC_CONNECTION_FACTORY = 'topic'
    
	def __init__(self, name, jndiName, busName, parent = Cell(), type = None):
		SIResource.__init__(self)
		self.name     = name
		self.jndiName = jndiName
		self.busName  = busName
		self.type     = type
		self.parent   = parent
		
	def __create__(self, update):
		params = self.__collectattrs__()
		print "Configuring SIBJMSConnectionFactory under %s scope with attributes '%s'" % (self.__scope__.split('#')[1].split('_')[0], params)
		if update:
			AdminTask.modifySIBJMSConnectionFactory(self.__scope__, params)
		else:
			AdminTask.createSIBJMSConnectionFactory(self.__scope__, params)
		
	def removeAll(self):
		args  = '[ -type %s]' % self.type
		for id in AdminTask.listSIBJMSConnectionFactories(self.__scope__, args).splitlines():
			print "Deleting SIBJMSConnectionFactory %s" % id.split('(')[0]
			AdminTask.deleteSIBJMSConnectionFactory(id)

class SIBJMSQueueConnectionFactory(SIBJMSConnectionFactory):
	def __init__(self, name, jndiName, busName, parent = Cell()):
		SIBJMSConnectionFactory.__init__(self, name, jndiName, busName, parent, SIBJMSConnectionFactory.QUEUE_CONNECTION_FACTORY)

class SIBJMSTopicConnectionFactory(SIBJMSConnectionFactory):
	def __init__(self, name, jndiName, busName, parent = Cell()):
		SIBJMSConnectionFactory.__init__(self, name, jndiName, busName, parent, SIBJMSConnectionFactory.TOPIC_CONNECTION_FACTORY)

class SIBJMSTopic(SIResource):
	DEF_ID    = '/SIBJMSTopic:%(name)s/'
	DEF_ATTRS = {
                "name" : None,
            "jndiName" : None,
         "description" : None,
           "topicName" : None,
          "topicSpace" : None,
        "deliveryMode" : None,
          "timeToLive" : None,
            "priority" : None,
           "readAhead" : None,
             "busName" : None,
	}
	
	def __init__(self, name, jndiName, parent = Cell()):
		SIResource.__init__(self)
		self.name     = name
		self.jndiName = jndiName
		self.parent   = parent
		
	def __create__(self, update):
		params = self.__collectattrs__()
		print "Configuring SIBJMSTopic under %s scope with attributes '%s'" % (self.__scope__.split('#')[1].split('_')[0], params)
		if update:
			AdminTask.modifySIBJMSTopic(self.__scope__, params)
		else:
			AdminTask.createSIBJMSTopic(self.__scope__, params)
	
	def removeAll(self):
		for id in AdminTask.listSIBJMSTopics(self.__scope__).splitlines():
			print "Deleting SIBJMSTopic %s" % id.split('(')[0]
			AdminTask.deleteSIBJMSTopic(id)

class SIBDestination(SIResource):
	DEF_ID    = '/SIBDestination:%(name)s/',
	DEF_ATTRS = {
                "bus" : None,
               "name" : None,
               "type" : None,
	}
	
	def __init__(self, name, parent = Cell()):
		SIResource.__init__(self)
		self.name   = name
		self.parent = parent
		
	def __create__(self, update):
		params = self.__collectattrs__()
		if update:
			AdminTask.modifySIBDesination(params)
		else:
			AdminTask.createSIBDestination(params)
		
	def removeAll(self):
		raise NotImplementedError("WARN: SIBDestination.removeAll() not implemented. SIBBus.removeAll() does the job...")

class SIBJMSQueue(SIResource):
	DEF_ID    = '/SIBJMSQueue:%(name)s/'
	DEF_ATTRS = {
                "name" : None,
            "jndiName" : None,
			 "cluster" : None,
         "description" : None,
           "queueName" : None,
        "deliveryMode" : None,
          "timeToLive" : None,
            "priority" : None,
           "readAhead" : None,
             "busName" : None,
              "server" : None,
               "node"  : None,
	}
	
	def __init__(self, name, jndiName, parent = Cell()):
		SIResource.__init__(self)
		self.name     = name
		self.jndiName = jndiName
		self.parent   = parent
		
	def __create__(self, update):
		if self.queueName is None:
			self.queueName = '_SYSTEM.Exception.Destination.%s.%s-%s' % (
					Node().getName(), 
					getServerName(self.parent.getAdminServers()[0]), 
					self.busName
			)
		
		params = self.__collectattrs__()
		print "Configuring SIBJMSQueue under %s scope with attributes '%s'" % (self.scope.split('#')[1].split('_')[0], params)
		if update:
			AdminTask.modifySIBJMSQueue(self.__scope__, params)
		else:
			AdminTask.createSIBJMSQueue(self.__scope__, params)
		
	def assignDestinationToManagedServerOrCluster(self, serverOrCluster):
		cell = self.parent
		
		if cell.isClustered():
			clusterName = cell.getCluster(serverOrCluster).getName()
			if not clusterName is None:
				self.cluster = clusterName
		else:
			managedServerId = cell.getManagedServers()[0]
			serverName  = getServerName(managedServerId)
			nodeName    = getNodeName(managedServerId)
			self.server = serverName
			self.node   = nodeName
	
	def removeAll(self):
		for id in AdminTask.listSIBJMSQueues(self.__scope__).splitlines():
			print "Deleting SIBJMSQueue %s" % id.split('(')[0]
			AdminTask.deleteSIBJMSQueue(id)

class SIBJMSActivationSpec(SIResource):
	DEF_ID    = '/J2CActivationSpec:%(name)s/'
	DEF_ATTRS = {
                           'name' : None,
                       'jndiName' : None,
            'destinationJndiName' : None,
                        'busName' : None,
                    'description' : None,
                'acknowledgeMode' : None,
            'authenticationAlias' : None,
                       'clientId' : None,
                'destinationType' : None,
        'durableSubscriptionHome' : None,
                   'maxBatchSize' : None,
                 'maxConcurrency' : None,
          'messageSelectorstring' : None,
                       'password' : None,
         'subscriptionDurability' : None,
               'subscriptionName' : None,
      'shareDurableSubscriptions' : None,
                       'userName' : None
	}
	
	def __init__(self, name, jndiName, destinationJndiName, busName, parent = Cell()):
		SIResource.__init__(self)
		self.parent              = parent
		self.name                = name
		self.jndiName            = jndiName
		self.destinationJndiName = destinationJndiName
		self.busName             = busName
		
	def __create__(self, update):
		params = self.__collectattrs__()
		print "Configuring J2CActivationSpec under %s scope with attributes '%s'" % (self.scope.split('#')[1].split('_')[0], params)
		if update:
			AdminTask.modifySIBJMSActivationSpec(self.__scope__, params)
		else:
			AdminTask.createSIBJMSActivationSpec(self.__scope__, params)
		
	def removeAll(self):
		for id in AdminConfig.list('J2CActivationSpec').splitlines():
			print 'Deleting J2CActivationSpec %s' % id.split('(')[0]
			AdminTask.deleteSIBJMSActivationSpec(id)
