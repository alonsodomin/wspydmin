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

from net.sf.wspydmin           import AdminConfig, AdminControl
from net.sf.wspydmin.topology  import Cell
from net.sf.wspydmin.resources import Resource

class JAASAuthData(Resource):
	DEF_ID    = '/JAASAuthData:%(alias)s/'
	DEF_ATTRS = {
              'alias' : None,
             'userId' : None,
           'password' : None,
        'description' : None
	}
	
	def __init__(self, alias, parent = Security()):
		Resource.__init__(self)
		self.alias  = alias
		self.parent = parent
	
	def __getconfigid__(self, id = None):
		for res in AdminConfig.list(self.__wastype__).splitlines():
			if (not res is None) and (res != '') and (self.alias == AdminConfig.showAttribute(res, 'alias')):
				return res
		return None

class Security(Resource):
	DEF_ID    = '%(scope)sSecurity:/'
	DEF_ATTRS = {
              'CSI' : None,
			  'IBM' : None
              #TODO: there is a bunch of other attributes.
              #TODO: now only supports CommonSecureInterop
	}
	
	def __init__(self, parent = Cell()):
		self.parent = parent
	
	def getCsiIIOPSecurityProtocol(self):
		id = AdminConfig.showAttribute(self.__getconfigid__(), 'CSI')
		return IIOPSecurityProtocol(id, self)

	def getIbmIIOPSecurityProtocol(self):
		id = AdminConfig.showAttribute(self.__getconfigid__(), 'IBM')
		return IIOPSecurityProtocol(id, self)

class IIOPSecurityProtocol(Resource):
	DEF_ID    = '/IIOPSecurityProtocol:/'
	DEF_ATTRS = { }
	
	def __init__(self, wasid, parent = Security()):
		Resource.__init__(self)
		self.__wasid  = wasid
		self.inbound  = self.getInboundConfiguration()
		self.outbound = self.getOutboundConfiguration()
		self.parent   = parent
		
	def __create__(self, update):
		self.inbound.__create__(update)
		self.outbound.__create__(update)
	
	def __getconfigid__(self):
		return self.__wasid
	
	def __loadattrs__(self):
		Resource.__loadattrs__(self)
		if not self.exists(): return
		
		id = AdminConfig.showAttribute(self.__getconfigid__(), 'claims')
		if not id is None:
			self.claims = CommonSecureInterop(id, self)
			
		id = AdminConfig.showAttribute(self.__getconfigid__(), 'performs')
		if not id is None:
			self.performs = CommonSecureInterop(id, self)
	
	def __remove__(self, deep):
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__wastype__

	def disableAuthentication(self):
		self.inbound.disableAuthentication()
		self.outbound.disableAuthentication()

	def enableTCPIPTransport(self):
		self.inbound.enableTCPIPTransport()
		self.outbound.enableTCPIPTransport()

class CommonSecureInterop(Resource):
	DEF_ID    = '/CommonSecureInterop:/'
	DEF_ATTRS = { }
	
	def __init__(self, wasid, parent):
		Resource.__init__(self)
		self.__wasid        = wasid
		self.messageLayer   =  self.getMessageLayer()
		self.transportLayer =  self.getTransportLayer()
		self.parent         = parent
		
	def __create__(self, update):
		self.messageLayer.__create__(update)
		self.transportLayer.__create__(update)
	
	def __getconfigid__(self):
		return self.__wasid
	
	def __remove__(self, deep):
		NotImplementedError, "%s.remove* method disabled for security reasons." % self.__wastype__
	
	def getMessageLayer(self):
		id = filter(
			lambda x: x.find('MessageLayer') > 0,
			AdminConfig.showAttribute(self.__getconfigid__(), 'layers')[1:-1].split()
		)[0]
		
		return MessageLayer(id, self)
    
	def getTransportLayer(self):
		id = filter(
			lambda x: x.find('TransportLayer') > 0,
			AdminConfig.showAttribute(self.__getconfigid__(), 'layers')[1:-1].split()
		)[0]
		
		return TransportLayer(id, self)
	
	def getIdentityAssertionLayer(self):
		raise NotImplementedError, "Method not implemented yet."

	def disableAuthentication(self):
		self.messageLayer.disableBasicAuthentication()
		self.transportLayer.disableClientCertificateAuthentication()
	
	def enableTCPIPTransport(self):
		self.transportLayer.enableTCPIPTransport()

class Layer(Resource):
	DEF_ID    = '/Layer:/'
	DEF_ATTRS = {
		'supportedQOP' : None,
		 'requiredQOP' : None
	}
	
	def __init__(self, wasid, parent):
		Resource.__init__(self)
		self.__wasid = wasid
		self.parent  = parent
		
	def __getattr__(self, name):
		if (name in Layer.DEF_ATTRS.keys()) and (self.__wasattrmap__[name] is None):
			obj = self.__getattrobj__(name)
			self.__wasattrmap__[name] = obj
			return obj
		else:
			return Resource.__getattr__(self, name)
	
	def __getattrobj__(self, name):
		raise NotImplementedError, "Provider an implementation for %s.getSupportedQOP()." % self.__wastype__
	
	def __getconfigid__(self, id = None):
		return self.__wasid

	def __create__(self, update):
		raise NotImplementedError, "%s.create* method disabled for security reasons." % self.__wastype__
		
	def __remove__(self, deep):
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__wastype__

class MessageLayer(Layer):

	def __init__(self, wasid, parent):
		Layer.__init__(self, wasid, parent)

	def __create__(self, update):
		self.supportedQOP.__create__(update)
	
	def __getattrobj__(self, name):
		id = AdminConfig.showAttribute(self.__getconfigid__(), name)
		return MessageQOP(id, self)

	def disableBasicAuthentication(self):
		self.supportedQOP.establishTrustInClient = 'false'
	
class TransportLayer(Layer):
	
	def __init__(self, wasid, parent):
		Layer.__init__(self, wasid, parent)
	
	def __create__(self, update):
		self.supportedQOP.__create__(update)
	
	def __getattrobj__(self, name):
		id = AdminConfig.showAttribute(self.__getconfigid__(), name)
		return TransportQOP(id, self)
	
	def disableClientCertificateAuthentication(self):
		self.supportedQOP.establishTrustInClient = 'false'
	
	def enableTCPIPTransport(self):
		self.supportedQOP.enableProtection = 'false'

class MessageQOP(Resource):
	DEF_ID    = '/MessageQOP:/'
	DEF_ATTRS = {
       'enableOutOfSequenceDetection' : None,
              'enableReplayDetection' : None,
             'establishTrustInClient' : None
	}
	
	def __init__(self, wasid, parent):
		Resource.__init__(self)
		self.__wasid = wasid
		self.parent  = parent
		
	def __getconfigid__(self, id = None):
		return self.__wasid
	
	def __remove__(self, deep):
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__wastype__

class TransportQOP(Resource):
	DEF_ID    = '/TransportQOP:/'
	DEF_ATTRS = {
                          'integrity' : None,
                    'confidentiality' : None,
                   'enableProtection' : None,
             'establishTrustInClient' : None
	}
	
	def __init__(self, wasid, parent):
		Resource.__init__(self)
		self.__wasid = wasid
		self.parent    = parent
	
	def __getconfigid__(self, id = None):
		return self.__wasid
	
	def __remove__(self, deep):
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__wastype__
