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
from net.sf.wspydmin.admin      import Cell
from net.sf.wspydmin.properties import Property

class PMIService(Resource):
	DEF_ID    = '/Cell:%(cell)s/Node:%(node)s/Server:%(server)s/'
	DEF_SCOPE = None
	DEF_ATTRS = {
		           'enable' : None,
		 'initialSpecLevel' : None,
		     'statisticSet' : None,
		'syncronizedUpdate' : None
	}
	
	def __init__(self, node, server, parent = Cell()):
		Resource.__init__(self)
		self.parent         = parent
		self.__properties__ = {}

	def __collectattrs__(self):
		attrs = self.__super__.__collectattrs__(self)
		props = []
		for name, prop in self.__properties__.items():
			props.append( [ name, prop.value ] )
		attrs.append( props )
		return attrs
	
	def __getconfigid__(self):
		return AdminConfig.list(self.__type__, self.__id__).splitlines()[0]

	def getProperty(self, name):
		return self.__properties__[name].value
	
	def setProperty(self, name, value):
		prop = Property(self)
		prop.name  = name
		prop.value = value
		self.__properties__[name] = prop
