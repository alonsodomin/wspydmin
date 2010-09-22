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
from net.sf.wspydmin.topology   import Cell
from net.sf.wspydmin.resources  import Resource
from net.sf.wspydmin.pool       import ConnectionPool

class JMSProvider(Resource):
	DEF_ID    = '%(scope)sJMSProvider:%(name)s/'
	DEF_ATTRS = {
				'name' : None
	}
	
	def __init__(self, name, parent = Cell()):
		Resource.__init__(self)
		self.name   = name
		self.parent = parent

class MQJMSProvider(JMSProvider):
	JMS_PROVIDER_NAME = 'WebSphere MQ JMS Provider'
	
	def __init__(self, parent = Cell()):
		JMSProvider.__init__(self, MQJMSProvider.JMS_PROVIDER_NAME, parent)

class MQQueueConnectionFactory(Resource):
	DEF_ID    = '%(scope)sMQQueueConnectionFactory:%(name)s/'
	DEF_TPL   = 'Example non-XA WMQ QueueConnectionFactory'
	DEF_ATTRS = {
                    'name' : None,
                'jndiName' : None,
                    'host' : None,
                    'port' : None,
            'queueManager' : None,
           'transportType' : None,
                 'channel' : None
	}
	
	def __init__(self, name):
		self.__wassuper__()
		self.name   = name
		self.parent = MQJMSProvider()
		
	def getConnectionPool(self):
		return ConnectionPool(self, 0)
	
	def getSessionPool(self):
		return ConnectionPool(self, 1)
	
	def setHostAndPort(self, host, port):
		self.host = host
		self.port = port

class MQQueue(Resource):
	DEF_ID    = '/MQQueue:%(name)s/'
	DEF_TPL   = 'Example.JMS.WMQ.Q1'
	DEF_ATTRS = {
                    'name' : None,
                'jndiName' : None,
            'targetClient' : None,
           'baseQueueName' : None,
    'baseQueueManagerName' : None
	}
	
	def __init__(self, name):
		self.__wassuper__()
		self.name   = name
		self.parent = MQJMSProvider()
