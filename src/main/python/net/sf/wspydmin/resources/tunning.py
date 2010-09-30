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

from net.sf.wspydmin      import AdminConfig
from net.sf.wspydmin.lang import Resource

class TunningParams(Resource):
	DEF_CFG_PATH    = '%(scope)sTuningParams:/'
	DEF_CFG_ATTRS = {
                "allowOverflow" : "false",
         "invalidationSchedule" : None,
          "invalidationTimeout" : 30,
      "maxInMemorySessionCount" : 1000,
         "scheduleInvalidation" : "false",
          "usingMultiRowSchema" : "false",
                "writeContents" : "ONLY_UPDATED_ATTRIBUTES",
               "writeFrequency" : "TIME_BASED_WRITE",
                "writeInterval" : "10"
	}
	
	def __init__(self, parent):
		Resource.__init__(self)
		self.parent = parent
	
	def __getconfigid__(self, id = None):
		return AdminConfig.list(self.__was_cfg_type__, self.parent.__getconfigid__())

class SessionManager(Resource):
	DEF_CFG_PATH    = '%(scope)sSessionManager:/'
	DEF_CFG_ATTRS = {
            "accessSessionOnTimeout" : "true",
      "allowSerializedSessionAccess" : "false",
                           "context" : None,
             "defaultCookieSettings" : None,
                            "enable" : "true",
                     "enableCookies" : "true",
     "enableProtocolSwitchRewriting" : "false",
                 "enableSSLTracking" : "false",
         "enableSecurityIntegration" : "false",
                "enableUrlRewriting" : "false",
                       "maxWaitTime" : 5,
                        "properties" : None,
        "sessionDatabasePersistence" : None,
            "sessionPersistenceMode" : "NONE",
                     "tunningParams" : None
	}
	
	def __init__(self, parent):
		Resource.__init__(self)
		self.parent      = parent
		#self.__tunning__ = TunningParams(self.parent)
		self.__tunning = TunningParams(self)

	def __wasinit__(self):
		Resource.__wasinit__(self)
		self.tunningParams = self.__tunning.__getconfigid__()

	def __getconfigid__(self, id = None):
		return AdminConfig.list(self.__was_cfg_type__, self.parent.__getconfigid__())

	def __getattr__(self, name):
		if (name == 'tunningParams'):
			return self.__tunning
		else:
			return Resource.__getattr__(self, name)
	
	def __setattr__(self, name, value):
		if (name == 'tunningParams'):
			raise AttributeError, "'tunningParams' is not writeable"
		else:
			Resource.__setattr__(self, name, value)

class ThreadPool(Resource):
	DEF_CFG_PATH    = '/ThreadPool:%(name)s/'
	DEF_CFG_ATTRS = {
      "customProperties" : None,
     "inactivityTimeout" : None,
            "isGrowable" : None,
           "maximumSize" : None,
           "minimumSize" : None,
                  "name" : None                 
	}
	
	def __init__(self, name, parent):
		Resource.__init__(self)
		self.parent  = parent
		self.name    = name	#WAS attribute
		self.__wasid = None
	
	def __getconfigid__(self, id = None):
		if self.__wasid is None:
			for tp in AdminConfig.list(self.__was_cfg_type__, self.parent.__getconfigid__()).splitlines():
				if AdminConfig.showAttribute(tp, 'name') == self.name:
					self.__wasid = tp
					break
		return self.__wasid

