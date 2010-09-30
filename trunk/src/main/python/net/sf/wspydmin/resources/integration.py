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

import logging

from net.sf.wspydmin                     import AdminConfig, AdminControl, AdminTask
from net.sf.wspydmin.lang                import Resource
from net.sf.wspydmin.resources.jdbc      import DataSource
from net.sf.wspydmin.resources.topology  import Cell, Node, Server, Cluster

class SIResource(Resource):
	
	def __getconfigid__(self):
		raise NotImplementedError, "ERROR: %s.__getconfigid__() not implemented" % self.__was_cfg_type__
	
	def __collectattrs__(self):
		str = ''
		for label, value in self.__was_cfg_attrmap.items():
			if not value is None:
				str = '%s -%s %s' % (str, label, value)
		return str

class SIBus(SIResource):
	DEF_CFG_PATH    = '/SIBus:%(bus)s/'
	DEF_CFG_ATTRS = {
                        'bus' : None,                      
                'busSecurity' : None, 
                'description' : None,
        'mediationsAuthAlias' : None,
                   'protocol' : None,
            'discardOnDelete' : None
	}
	
	def __init__(self, name, parent = Cell()):
		SIResource.__init__(self)
		self.bus          = name
		self.parent       = parent
		self.__busmembers = []
		
	def __create__(self, update):    
		params = self.__collectattrs__()
		logging.info("Configuring SIBus with attributes %s" % params)
		if update:
			AdminTask.modifySIBus(params)
		else:
			AdminTask.createSIBus(params)
        
		for busMember in self.__busmembers:
			busMember.__create__(update)
	
	def addApplicationServerAsBusMember(self, nodeName, serverName):
		member        = SIBusMember( self.bus )
		member.node   = nodeName
		member.server = serverName
		self.addSIBusMember(member)
	
	def addSIBusMember(self, siBusMember):
		self.__busmembers.append(siBusMember)
	
	def addClusterServerAsBusMember(self, clusterName, storeType='file'):
		member         = SIBusMember( self.bus )
		member.cluster = clusterName
		
		if (storeType=='file'):
			member.fileStore               = ''
			member.logDirectory            = 'CL_busMember_logDir_' + clusterName
			member.permanentStoreDirectory = 'CL_busMember_permStoreDir_' + clusterName
			member.temporaryStoreDirectory = 'CL_busMember_tempStoreDir_' + clusterName
		else:
			raise NotImplementedException('please implement the Datastore feature for cluster bus members')
        
		self.addSIBusMember(member)
	
	def addServerAsBusMember(self, serverName):
		member        = SIBusMember( self.bus )
		member.server = serverName
		self.addSIBusMember(member)
    
	def addWmqServerAsBusMember(self, wmqServerName):
		member           = SIBusMember( self.bus )
		member.wmqServer = wmqServerName
		self.addSIBusMember(member)
	
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
	DEF_CFG_PATH    = '/SIBusMember:%(bus)s/'
	DEF_CFG_ATTRS = {
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
		logging.info( "Configuring SIBusMember with attributes %s" % params )
		if update:
			AdminTask.modifySIBusMember(params)
		else:
			AdminTask.addSIBusMember(params)
	
	def remove(self):
		logging.warning("SIBusMember.remove() not implemented. User SIBus.remove() instead.")

	def removeAll(self):
		logging.warning("SIBusMember.removeAll() not implemented. User SIBus.removeAll() instead.")

class SIBJMSConnectionFactory(SIResource):
	DEF_CFG_PATH    = '/SIBJMSConnectionFactory:%(name)s/'
	DEF_CFG_ATTRS = {
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
		logging.info("Configuring SIBJMSConnectionFactory under %s scope with attributes '%s'" % (self.__was_cfg_parent__.split('#')[1].split('_')[0], params))
		if update:
			AdminTask.modifySIBJMSConnectionFactory(self.__was_cfg_parent__, params)
		else:
			AdminTask.createSIBJMSConnectionFactory(self.__was_cfg_parent__, params)
		
	def removeAll(self):
		args  = '[ -type %s]' % self.type
		for id in AdminTask.listSIBJMSConnectionFactories(self.__was_cfg_parent__, args).splitlines():
			logging.info("Deleting SIBJMSConnectionFactory %s" % id.split('(')[0]))
			AdminTask.deleteSIBJMSConnectionFactory(id)

class SIBJMSQueueConnectionFactory(SIBJMSConnectionFactory):
	def __init__(self, name, jndiName, busName, parent = Cell()):
		SIBJMSConnectionFactory.__init__(self, name, jndiName, busName, parent, SIBJMSConnectionFactory.QUEUE_CONNECTION_FACTORY)

class SIBJMSTopicConnectionFactory(SIBJMSConnectionFactory):
	def __init__(self, name, jndiName, busName, parent = Cell()):
		SIBJMSConnectionFactory.__init__(self, name, jndiName, busName, parent, SIBJMSConnectionFactory.TOPIC_CONNECTION_FACTORY)

class SIBJMSTopic(SIResource):
	DEF_CFG_PATH    = '/SIBJMSTopic:%(name)s/'
	DEF_CFG_ATTRS = {
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
		logging.info("Configuring SIBJMSTopic under %s scope with attributes '%s'" % (self.__was_cfg_parent__.split('#')[1].split('_')[0], params))
		if update:
			AdminTask.modifySIBJMSTopic(self.__was_cfg_parent__, params)
		else:
			AdminTask.createSIBJMSTopic(self.__was_cfg_parent__, params)
	
	def removeAll(self):
		for id in AdminTask.listSIBJMSTopics(self.__was_cfg_parent__).splitlines():
			logging.info("Deleting SIBJMSTopic %s" % id.split('(')[0])
			AdminTask.deleteSIBJMSTopic(id)

class SIBDestination(SIResource):
	DEF_CFG_PATH    = '/SIBDestination:%(name)s/',
	DEF_CFG_ATTRS = {
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
	DEF_CFG_PATH    = '/SIBJMSQueue:%(name)s/'
	DEF_CFG_ATTRS = {
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
		logging.info("Configuring SIBJMSQueue under %s scope with attributes '%s'" % (self.scope.split('#')[1].split('_')[0], params))
		if update:
			AdminTask.modifySIBJMSQueue(self.__was_cfg_parent__, params)
		else:
			AdminTask.createSIBJMSQueue(self.__was_cfg_parent__, params)
		
	def assignDestinationToManagedServerOrCluster(self, serverOrCluster):
		cell = self.parent
		
		if cell.isClustered():
			clusterName = cell.getCluster(serverOrCluster).getName()
			if not clusterName is None:
				self.cluster = clusterName
		else:
			managedServerId = cell.getManagedServers()[0]
			self.server     = getServerName(managedServerId)
			self.node       = getNodeName(managedServerId)
	
	def removeAll(self):
		for id in AdminTask.listSIBJMSQueues(self.__was_cfg_parent__).splitlines():
			logging.info("Deleting SIBJMSQueue %s" % id.split('(')[0])
			AdminTask.deleteSIBJMSQueue(id)

class SIBJMSActivationSpec(SIResource):
	DEF_CFG_PATH    = '/J2CActivationSpec:%(name)s/'
	DEF_CFG_ATTRS = {
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
		logging.info("Configuring J2CActivationSpec under %s scope with attributes '%s'" % (self.scope.split('#')[1].split('_')[0], params))
		if update:
			AdminTask.modifySIBJMSActivationSpec(self.__was_cfg_parent__, params)
		else:
			AdminTask.createSIBJMSActivationSpec(self.__was_cfg_parent__, params)
		
	def removeAll(self):
		for id in AdminConfig.list('J2CActivationSpec').splitlines():
			logging.info('Deleting J2CActivationSpec %s' % id.split('(')[0])
			AdminTask.deleteSIBJMSActivationSpec(id)
