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

from net.sf.wspydmin            import AdminConfig, AdminControl
from net.sf.wspydmin.resources  import Resource

class TransactionService(Resource):
	DEF_ID    = '/TransactionService:/'
	DEF_ATTRS = {
                'LPSHeuristicCompletion' : 'ROLLBACK',
                  'asyncResponseTimeout' : 30,
               'clientInactivityTimeout' : 60,
                                'enable' : 'true',
                     'enableFileLocking' : 'true',
    'enableLoggingForHeuristicReporting' : 'false',
                'enableProtocolSecurity' : 'true',
                   'heuristicRetryLimit' : 0,
                    'heuristicRetryWait' : 0,
                       'httpProxyPrefix' : None,
                      'httpsProxyPrefix' : None,
             'maximumTransactionTimeout' : 0,
                            'properties' : None,
    'propogatedOrBMTTranLifetimeTimeout' : 300,
              'totalTranLifetimeTimeout' : 120,
                  'waitForCommitOutcome' : 'false',
	}
	
	def __init__(self, parent):
		self.parent = parent
	
	def __getconfigid__(self, id = None):
		return AdminConfig.list(self.__type__, self.parent.__getconfigid__()).splitlines()[0]

