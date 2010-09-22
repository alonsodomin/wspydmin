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

from java.lang                 import UnsupportedOperationException

from net.sf.wspydmin           import AdminConfig, AdminControl, AdminTask
from net.sf.wspydmin.mbean     import ResourceMBean
from net.sf.wspydmin.resources import Resource
from net.sf.wspydmin.tunning   import ThreadPool
from net.sf.wspydmin.utils     import *

class MessageListenerService(Resource):
	DEF_ID    = '/MessageListenerService:/'
	DEF_ATTRS = {
                            'enable' : 'false',
                           'context' : None,
                     #'listenerPorts' : [],
             'maxMDBListenerRetries' : 5,
       'mdbListenerRecoveryInterval' : 60,
             'mqJMSPoolingThreshold' : 10,
               'mqJMSPoolingTimeout' : 300000,
                        'properties' : [],
                        #'threadPool' : None
	}
	
	def __init__(self, parent):
		Resource.__init__(self)
		self.parent     = parent
		self.nodeName   = parent.nodeName
		self.serverName = parent.serverName
		
	def __loadattrs__(self):
		def excludes(x): return not {'threadPool' : None, 'listenerPorts':None}.has_key(x[0])
		if self.exists():
			for name, value in filter(excludes, map(splitAttrs, AdminConfig.show(self.__getconfigid__()).splitlines())):
				self.__wasattrmap__[name] = self.__parseattr__(name, value)
	
	def __getconfigid__(self):
		id = AdminConfig.list(self.__wastype__, self.parent.__getconfigid__())
		if (id is None) or (id == ''):
			return None
		else:
			return id
	
	def getListenerPorts(self):
		lps = {}
		if not self.exists():
			return lps #Nothing to do as there is no MessageListenerService available on this server 
        
		for lpname in map(lambda x: x.split('(')[0], AdminConfig.list('ListenerPort', self.__getconfigid__()).splitlines()):
			lps[lpname] = ListenerPort(lpname, self)
		return lps
	
	def getNewListenerPort(self, name):
		return ListenerPort(name, self)

	def removeListenerPort(self, name):
		lps = self.getListenerPorts()
		if lps.has_key(name):
			lps[name].remove()
	
	def getThreadPool(self):
		return ThreadPool('Message.Listener.Pool', self)

	def remove(self):
		raise UnsupportedOperationException, "WARN: Message Listener Service can't be removed. Nothing done."
    
	def removeAll(self):
		for name, lp in self.getListenerPorts().items():
			lp.remove()

class ListenerPort(ResourceMBean):
	DEF_ID      = '/ListenerPort:%(name)s/'
	DEF_ATTRS   = {
                             'name' : None,
                      'description' : None,
        'connectionFactoryJNDIName' : None,
              'destinationJNDIName' : None,
                      'maxSessions' : 1,
                       'maxRetries' : 0,
                      'maxMessages' : 1,
                  'stateManagement' : None,
               'statisticsProvider' : None
	}
	DEF_METHODS  = [ 'start', 'stop' ]
	
	DEF_INITIAL = 'START'
	
	def __init__(self, name, parent):
		ResourceMBean.__init__(self)
		self.name         = name
		self.parent       = parent
		self.nodeName     = parent.nodeName
		self.serverName   = parent.serverName
		self.initialState = ListenerPort.DEF_INITIAL
		self.__statemng   = StateManageable(self)
		
	def __create__(self, update):
		ResourceMBean.__create__(self, update)
		if self.initialState != ListenerPort.DEF_INITIAL:
			self.__statemng.update()
	
	def __getconfigid__(self, id = None):
		for lpid in AdminConfig.list(self.__wastype__, self.parent.__getconfigid__()).splitlines():
			if lpid.startswith(self.name):
				return lpid
		return None
	
	def isStarted(self):
		return (AdminControl.getAttribute(self.__getmbeanid__(), 'started') == 'true')
	
class StateManageable(Resource):
	DEF_ID    = '%(scope)sStateManageable:/'
	DEF_ATTRS = {
        'initialState' : 'START'      
	}
	
	def __init__(self, parent, initialState = 'START'):
		Resource.__init__(self)
		self.parent       = parent
		self.initialState = initialState
	
	def __getconfigid__(self, id = None):
		return AdminConfig.list(self.__wastype__, self.parent.__getconfigid__()).splitlines()[0]
	
	def removeAll(self):
		raise UnsupportedOperationException, "Use ListenerPort.removeAll() instead of StateManageable.removeAll()"
