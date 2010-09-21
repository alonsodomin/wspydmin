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

from net.sf.wspydmin           import AdminConfig
from net.sf.wspydmin.resources import Resource

class ConnectionPool(Resource):
	DEF_ID    = '%(scope)sConnectionPool:/'
	DEF_ATTRS = {
                            'agedTimeout' : 0,
                      'connectionTimeout' : 180,
          'freePoolDistributionTableSize' : 0,
                         'maxConnections' : 10,
                         'minConnections' : 1,
             'numberOfFreePoolPartitions' : 0,
           'numberOfSharedPoolPartitions' : 0,
         'numberOfUnsharedPoolPartitions' : 0,
                             'properties' : [],
                            'purgePolicy' : 'EntirePool',
                               'reapTime' : 180,
                         'stuckThreshold' : 0,
                              'stuckTime' : 0,
                         'stuckTimerTime' : 0,
                  'surgeCreationInterval' : 0,
                         'surgeThreshold' : -1,
                         'testConnection' : 'false',
                 'testConnectionInterval' : 0,
                          'unusedTimeout' : 1800
	}
	
	def __init__(self, parent, index = 0):
		Resource.__init__(self)
		self.parent = parent
		self.index  = index
	
	def __getconfigid__(self):
		return AdminConfig.getid(self.__id__).splitlines()[self.index]
