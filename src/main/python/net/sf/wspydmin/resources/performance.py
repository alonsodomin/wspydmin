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

from net.sf.wspydmin                      import AdminConfig, AdminControl
from net.sf.wspydmin.resources            import Resource
from net.sf.wspydmin.resources.topology   import CURRENT_CELL
from net.sf.wspydmin.resources.properties import PropertyHolderResource

class PMIService(PropertyHolderResource):
	DEF_CFG_PATH    = '%(scope)sNode:%(node)s/Server:%(server)s/'
	DEF_CFG_ATTRS = {
		           'enable' : None,
		 'initialSpecLevel' : None,
		     'statisticSet' : None,
		'syncronizedUpdate' : None
	}
	
	def __init__(self, node, server, parent = CURRENT_CELL):
		self.__wassuper__()
		self.node   = node
		self.server = server
		self.parent = parent
	
	def __getconfigid__(self):
		return AdminConfig.list(self.__was_cfg_type__, self.__was_cfg_path__).splitlines()[0]

