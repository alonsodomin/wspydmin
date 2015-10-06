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
from net.sf.wspydmin.lang                 import Resource
from net.sf.wspydmin.resources.topology   import Cell

class MailProvider(Resource):
	DEF_CFG_PATH = '%(scope)sMailProvider:%(name)s/'
	DEF_CFG_ATTRS = {
                    'name' : None,
	}
	
	def __init__(self, name, parent = Cell()):
		Resource.__init__(self)
		self.name   = name
		self.parent = parent

class DefaultMailProvider(MailProvider):
	MAIL_PROVIDER_NAME = 'Built-in Mail Provider'
	
	def __init__(self, parent = Cell()):
		MailProvider.__init__(self, DefaultMailProvider.MAIL_PROVIDER_NAME, parent)

class MailSession(Resource):
	DEF_CFG_PATH    = '%(scope)sMailSession:%(name)s/'
	DEF_CFG_ATTRS = {
                    'name' : None,
                'jndiName' : None,
                'mailFrom' : None,
       'mailTransportHost' : None
	}
	
	def __init__(self, name):
		self.__wassuper__()
		self.name   = name
		self.parent = DefaultMailProvider()

