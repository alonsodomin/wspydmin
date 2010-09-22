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

import sys, traceback

from net.sf.wspydmin               import AdminConfig, AdminControl
from net.sf.wspydmin.resources     import Resource

class ClassLoader(Resource):
	DEF_ID    = '/Classloader:/'
	DEF_ATTRS = {
        'mode' : None #PARENT_FIRST, PARENT_LAST
	}

	def __init__(self, targetResourceName):
		self.targetResourceName = targetResourceName
		
	def __getconfigid__(self):
		for targetName, id in map(
			lambda x: [x.split('|')[0].split('/')[-1], x],
			AdminConfig.list(self.__wastype__).splitlines()
		):
			if targetName == self.targetResourceName:
				return id
		
		return None
	
	def setParentFirstMode(self):
		self.mode = 'PARENT_FIRST'
    
	def setParentLastMode(self):
		self.mode = 'PARENT_LAST'

	def removeAll(self):
		raise NotImplementedError, "Not implemented for safety reasons."
