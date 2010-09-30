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

from net.sf.wspydmin                   import AdminConfig, AdminControl
from net.sf.wspydmin.lang              import Resource
from net.sf.wspydmin.resources.tunning import SessionManager

class WebContainer(Resource):
	DEF_CFG_PATH    = '/WebContainer:/'
	DEF_CFG_ATTRS = {
                'disablePooling' : 'false',
          'enableServletCaching' : 'false',
        'sessionAffinityTimeout' : 0
	}
	
	def __init__(self, parent):
		Resource.__init__(self)
		self.parent        = parent
		self.__sessionmngr = SessionManager(self)
	
	def __getconfigid__(self, id = None):
		return AdminConfig.list(self.__was_cfg_type__, self.parent.__getconfigid__()).splitlines()[0]
	
	def getSessionManager(self):
		return self.__sessionmngr
