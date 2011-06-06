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

import re

from net.sf.wspydmin                    import AdminConfig, AdminControl
from net.sf.wspydmin.resources          import Resource
from net.sf.wspydmin.resources.topology import CURRENT_CELL

class VariableMap(Resource):
	DEF_CFG_PATH = '%(scope)sVariableMap:/'
	
	def __init__(self, parent = CURRENT_CELL):
		Resource.__init__(self)
		self.parent   = parent
		self.__varmap = {}

	def addVariable(self, var):
		self.__varmap[var.symbolicName] = var

class VariableSubstitutionEntry(Resource):
	__parent_attrname__ = 'variableMap'
	
	DEF_CFG_PATH    = '%(scope)sVariableSubstitutionEntry:%(symbolicName)s/'
	DEF_CFG_ATTRS = {
			'symbolicName' : None,
			       'value' : None
	}
	
	def __init__(self, variableMap):
		Resource.__init__(self)
		self.variableMap = variableMap