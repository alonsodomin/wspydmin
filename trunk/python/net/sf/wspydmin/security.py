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

from net.sf.wspydmin           import AdminConfig, AdminControl
from net.sf.wspydmin.admin     import Cell
from net.sf.wspydmin.resources import Resource

class JAASAuthData(Resource):
	DEF_SCOPE = '/Cell:%s/Security:/' % AdminControl.getCell()
	DEF_ID    = '/JAASAuthData:%(alias)s/'
	DEF_TPL   = None
	DEF_ATTRS = {
              'alias' : None,
             'userId' : None,
           'password' : None,
        'description' : None
	}
	
	def __init__(self, alias):
		Resource.__init__(self)
		self.alias = alias
	
	def __getconfigid__(self, id = None):
		for res in AdminConfig.list(JAASAuthData.__TYPE__).splitlines():
			if (not res is None) and (res != '') and (self.alias == AdminConfig.showAttribute(res, 'alias')):
				return res
		return None

class Security(Resource):
	DEF_SCOPE = None
	DEF_ID    = '/Security:/'
	DEF_TPL   = None
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
		return IIOPSecurityProtocol(id)

	def getIbmIIOPSecurityProtocol(self):
		id = AdminConfig.showAttribute(self.__getconfigid__(), 'IBM')
		return IIOPSecurityProtocol(id)

class IIOPSecurityProtocol(Resource):
	DEF_SCOPE = None
	DEF_ID    = '/IIOPSecurityProtocol:/'
	DEF_TPL   = None
	DEF_ATTRS = { }
	
	def __init__(self, wasid):
		Resource.__init__(self)
		self.__wasid__ = wasid
		self.inbound   = self.getInboundConfiguration()
		self.outbound  = self.getOutboundConfiguration()
		
	def __create__(self, update):
		self.inbound.__create__(update)
		self.outbound.__create__(update)
	
	def __getconfigid__(self, id = None):
		return self.__wasid__
	
	def __remove__(self, deep):
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__type__
	
	def getInboundConfiguration(self):
		id = AdminConfig.showAttribute(self.__getconfigid__(), 'claims')
		return CommonSecureInterop(id)
    
	def getOutboundConfiguration(self):
		id = AdminConfig.showAttribute(self.__getconfigid__(), 'performs')
		return CommonSecureInterop(id)

	def disableAuthentication(self):
		self.inbound.disableAuthentication()
		self.outbound.disableAuthentication()

	def enableTCPIPTransport(self):
		self.inbound.enableTCPIPTransport()
		self.outbound.enableTCPIPTransport()

class CommonSecureInterop(Resource):
	DEF_SCOPE = None
	DEF_ID    = '/CommonSecureInterop:/'
	DEF_TPL   = None
	DEF_ATTRS = { }
	
	def __init__(self, wasid):
		Resource.__init__(self)
		self.__wasid__      = wasid
		self.messageLayer   =  self.getMessageLayer()
		self.transportLayer =  self.getTransportLayer()
		
	def __create__(self, update):
		self.messageLayer.__create__(update)
		self.transportLayer.__create__(update)
	
	def __getconfigid__(self, id = None):
		return self.__wasid__
	
	def __remove__(self, deep):
		NotImplementedError, "%s.remove* method disabled for security reasons." % self.__type__
	
	def getMessageLayer(self):
		id = filter(
			lambda x: x.find('MessageLayer') > 0,
			AdminConfig.showAttribute(self.__getconfigid__(), 'layers')[1:-1].split()
		)[0]
		
		return MessageLayer(id)
    
	def getTransportLayer(self):
		id = filter(
			lambda x: x.find('TransportLayer') > 0,
			AdminConfig.showAttribute(self.__getconfigid__(), 'layers')[1:-1].split()
		)[0]
		
		return TransportLayer(id)
	
	def getIdentityAssertionLayer(self):
		raise NotImplementedError, "Method not implemented yet."

	def disableAuthentication(self):
		self.messageLayer.disableBasicAuthentication()
		self.transportLayer.disableClientCertificateAuthentication()
	
	def enableTCPIPTransport(self):
		self.transportLayer.enableTCPIPTransport()

class Layer(Resource):
	DEF_SCOPE = None
	DEF_ID    = '/Layer:/'
	DEF_TPL   = None
	DEF_ATTRS = {
		'supportedQOP' : None,
		 'requiredQOP' : None
	}
	
	def __init__(self, wasid):
		Resource.__init__(self)
		self.__wasid__ = wasid
		
	def __getattr__(self, name):
		if (name in Layer.DEF_ATTRS.keys()) and (not self.__attrmap__.has_key(name)):
			obj = self.__getattrobj__(name)
			self.__attrmap__[name] = obj
			return obj
		else:
			return Resource.__getattr__(self, name)
	
	def __getattrobj__(self, name):
		raise NotImplementedError, "Provider an implementation for %s.getSupportedQOP()." % self.__type__
	
	def __getconfigid__(self, id = None):
		return self.__wasid__

	def __create__(self, update):
		raise NotImplementedError, "%s.create* method disabled for security reasons." % self.__type__
		
	def __remove__(self, deep):
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__type__

class MessageLayer(Layer):

	def __init__(self, wasid):
		Layer.__init__(self, wasid)

	def __create__(self, update):
		self.supportedQOP.__create__(update)
	
	def __getattrobj__(self, name):
		id = AdminConfig.showAttribute(self.__getconfigid__(), name)
		return MessageQOP(id)

	def disableBasicAuthentication(self):
		self.supportedQOP.establishTrustInClient = 'false'
	
class TransportLayer(Layer):
	
	def __init__(self, wasid):
		Layer.__init__(self, wasid)
	
	def __create__(self, update):
		self.supportedQOP.__create__(update)
	
	def __getattrobj__(self, name):
		id = AdminConfig.showAttribute(self.__getconfigid__(), name)
		return TransportQOP(id)
	
	def disableClientCertificateAuthentication(self):
		self.supportedQOP.establishTrustInClient = 'false'
	
	def enableTCPIPTransport(self):
		self.supportedQOP.enableProtection = 'false'

class MessageQOP(Resource):
	DEF_SCOPE = None
	DEF_ID    = '/MessageQOP:/'
	DEF_TPL   = None
	DEF_ATTRS = {
       'enableOutOfSequenceDetection' : None,
              'enableReplayDetection' : None,
             'establishTrustInClient' : None
	}
	
	def __init__(self, wasid):
		Resource.__init__(self)
		self.__wasid__ = wasid
		
	def __getconfigid__(self, id = None):
		return self.__wasid__
	
	def __remove__(self, deep):
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__type__

class TransportQOP(Resource):
	DEF_SCOPE = None
	DEF_ID    = '/TransportQOP:/'
	DEF_TPL   = None
	DEF_ATTRS = {
                          'integrity' : None,
                    'confidentiality' : None,
                   'enableProtection' : None,
             'establishTrustInClient' : None
	}
	
	def __init__(self, wasid):
		self.__wasid__ = wasid
	
	def __getconfigid__(self, id = None):
		return self.__wasid__
	
	def __remove__(self, deep):
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__type__
