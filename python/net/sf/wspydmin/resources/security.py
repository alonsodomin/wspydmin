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
from net.sf.wspydmin.resources.topology  import Cell

class JAASAuthData(Resource):
	DEF_CFG_PATH    = '/JAASAuthData:%(alias)s/'
	DEF_CFG_ATTRS = {
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
		for res in AdminConfig.list(self.__was_cfg_type__).splitlines():
			if (not res is None) and (res != '') and (self.alias == AdminConfig.showAttribute(res, 'alias')):
				return res
		return None

class Security(Resource):
	DEF_CFG_PATH    = '%(scope)sSecurity:/'
	DEF_CFG_ATTRS = {
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
	DEF_CFG_PATH    = '/IIOPSecurityProtocol:/'
	DEF_CFG_ATTRS = { }
	
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
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__was_cfg_type__

	def disableAuthentication(self):
		self.inbound.disableAuthentication()
		self.outbound.disableAuthentication()

	def enableTCPIPTransport(self):
		self.inbound.enableTCPIPTransport()
		self.outbound.enableTCPIPTransport()

class CommonSecureInterop(Resource):
	DEF_CFG_PATH    = '/CommonSecureInterop:/'
	DEF_CFG_ATTRS = { }
	
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
		NotImplementedError, "%s.remove* method disabled for security reasons." % self.__was_cfg_type__
	
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
	DEF_CFG_PATH    = '/Layer:/'
	DEF_CFG_ATTRS = {
		'supportedQOP' : None,
		 'requiredQOP' : None
	}
	
	def __init__(self, wasid, parent):
		Resource.__init__(self)
		self.__wasid = wasid
		self.parent  = parent
		
	def __getattr__(self, name):
		if (name in Layer.DEF_CFG_ATTRS.keys()) and (self.__was_cfg_attrmap__[name] is None):
			obj = self.__getattrobj__(name)
			self.__was_cfg_attrmap__[name] = obj
			return obj
		else:
			return Resource.__getattr__(self, name)
	
	def __getattrobj__(self, name):
		raise NotImplementedError, "Provider an implementation for %s.getSupportedQOP()." % self.__was_cfg_type__
	
	def __getconfigid__(self, id = None):
		return self.__wasid

	def __create__(self, update):
		raise NotImplementedError, "%s.create* method disabled for security reasons." % self.__was_cfg_type__
		
	def __remove__(self, deep):
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__was_cfg_type__

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
	DEF_CFG_PATH    = '/MessageQOP:/'
	DEF_CFG_ATTRS = {
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
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__was_cfg_type__

class TransportQOP(Resource):
	DEF_CFG_PATH    = '/TransportQOP:/'
	DEF_CFG_ATTRS = {
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
		raise NotImplementedError, "%s.remove* method disabled for security reasons." % self.__was_cfg_type__

#
# Security utilities
#

def installSignerCertificateInKeyStore(certFileName, keyStoreName):
	"""Installs a certificate file into the WebSphere's key store"""
    certFileLocation = certFileName
	logging.info('Preparing installation of certificate %s from file %s into store %s' % (certFileName, certFileLocation, keyStoreName))
    AdminTask.addSignerCertificate(['-keyStoreName', keyStoreName, '-certificateAlias', 
		'customcert_' + certFileName, '-certificateFilePath', certFileLocation, '-base64Encoded', 'true'])
	logging.info('certificate %s is installed in keystore %s' % (certFileName, keyStoreName))

def deleteCustomSignerCertificatesFromKeyStore(keyStoreName):
	"""Removes the custom certificates installed into the WebSphere's key store"""
	logging.info('Preparing removal of custom certificates from store %s' % (keyStoreName))

    certificateList = AdminTask.listSignerCertificates(['-keyStoreName', keyStoreName]).splitlines()
    for certificate in certificateList:
        certAlias = certificate.split('] [alias')[1].split('] [validity')[0]
        if (certAlias.find('customcert_') != -1):
            AdminTask.deleteSignerCertificate(['-keyStoreName', keyStoreName, '-certificateAlias', certAlias])
			logging.info('Certificate %s has been deleted' % (certAlias))
        else:
			logging.info('Certificate %s will not be deleted' % (certAlias))
