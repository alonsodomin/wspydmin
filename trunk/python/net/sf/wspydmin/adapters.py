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

from com.ibm.websphere.management.exception import AdminException
from com.ibm.ws.scripting                   import ScriptingException

from net.sf.wspydmin                        import AdminConfig, AdminControl
from net.sf.wspydmin                        import Cell   
from net.sf.wspydmin.resources              import Resource

class J2CResourceAdapter(Resource):
    DEF_ID    = '%(scope)sJ2CResourceAdapter:%(name)s/'
    DEF_ATTRS = {
                 'name' : None
    }
    
    def __init__(self, name):
        Resource.__init__(self)
        self.name   = name
        self.parent = Cell()
