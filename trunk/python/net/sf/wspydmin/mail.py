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

from net.sf.wspydmin            import AdminConfig, AdminControl
from net.sf.wspydmin.resources  import Resource

class MailSession(Resource):
	DEF_SCOPE = '/Cell:%s/MailProvider:Built-in Mail Provider/' % AdminControl.getCell()
	DEF_ID    = '/MailSession:%(name)s/'
	DEF_TPL   = None
	DEF_ATTRS = {
                    'name' : None,
                'jndiName' : None,
                'mailFrom' : None,
       'mailTransportHost' : None
	}

