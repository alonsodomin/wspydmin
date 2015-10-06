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
from net.sf.wspydmin.lang               import Resource
from net.sf.wspydmin.resources.topology import Cell

class VariableMap(Resource):
	DEF_CFG_PATH = '%(scope)sVariableMap:/'
	
	def __init__(self, parent = Cell()):
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
		
	
class VariableSubstitutionEntryHelper:
	def __init__(self):		
		self.vms = {
			'cells' : {},
		 'clusters' : {},
			'nodes' : {},
		  'servers' : {}
		}
		
		for vmid in AdminConfig.list('VariableMap').splitlines():
			vars = {}
			for varid in AdminConfig.list('VariableSubstitutionEntry',vmid).splitlines():
				name = AdminConfig.showAttribute(varid, 'symbolicName')
				vars[name] = {
						'id' : varid,
					  'name' : name,
					 'value' : AdminConfig.showAttribute(varid, 'value')
				}

			scope = vmid.split('/')[-1].split('|')[0]
			type  = vmid.split('/')[-2].replace('(', '')
			self.vms[type][scope] = { 
				'id' : vmid,
			  'vars' : vars
			}

	def getTypeForScope(self, scope):
		for type, ignore in self.vms.items():
			if self.vms[type].has_key(scope):
				return type
			
		return 'Unknown'
	
	def __call(self, function, name, value, scope = None, type = None):
		if scope is None: #we just apply given function under all scopes
			for type, ignore in self.vms.items():
				for scope, ignore in self.vms[type].items():
					self.__call(self.__call, name, value, scope, type)
			return
		
		if type is None: #discover type if unknown
			type = self.getTypeForScope(scope)
			
		if not self.vms.has_key(type):
			raise Exception, "Not valid scope type '%s'" % type
		
		if not self.vms[type].has_key(scope):
			raise Exception, "Not valid scope '%s' for type '%s'" % (scope, type)

		function(name, value, scope, type)
		
	def updateVariable(self, name, value, scope = None, type = None):
		"""Update variables under given scope of on every scope if this is None"""
		if scope is None or type is None:
			self.__call(self.updateVariable, name, value, scope, type)
		
		if self.vms[type][scope]['vars'].has_key(name):
			self.vms[type][scope]['vars'][name]['value'] = value 
			AdminConfig.modify(self.vms[type][scope]['vars'][name]['id'], [['value', value]])
			print "Variable '%s' to '%s' updated under scope '%s'." % (name, value, scope)
			return 1==1 # True, variable updated successfully
		
		return None #False, not updated
	
	def updateCellVariable(self, name, value):
		"""Update variables under Cell scope"""
		self.updateVariable(name, value, AdminControl.getCell(), 'cells')
	
	def updateClusterVariable(self, name, value):
		"""Update variables under Cluster scope"""
		for scope, ignore in self.vms['clusters'].items(): 
			self.updateVariable(name, value, scope, 'clusters')
		
	def updateNodeVariable(self, name, value):
		"""Update variables on each Node"""
		for scope, ignore in self.vms['nodes'].items():
			self.updateVariable(name, value, scope, 'nodes')
	
	def updateServerVariable(self, name, value):
		"""Update variables on each Server"""
		for scope, ignore in self.vms['servers'].items():
			self.updateVariable(name, value, scope)
			
	def setVariable(self, name, value, scope, type):
		"""Creates or updates a Variable on a given scope or on every scope if scope == None"""
		if scope is None or type is None:
			self.__call(self.setVariable, name, value, scope, type)
		
		if not self.updateVariable(name, value, scope, type):
			id = AdminConfig.create('VariableSubstitutionEntry', self.vms[type][scope]['id'],
					[ 
					  [ 'symbolicName', name  ], 
					  [ 'value',        value ] 
					] 
			)
				
			self.vms[type][scope]['vars'][name] = {
						'id' : id,
					  'name' : name,
					 'value' : value
			}
			print "New variable '%s' to '%s' created under scope '%s'." % (name, value, scope)
			
		return 1==1 # True
	
	def setCellVariable(self, name, value):
		"""Creates or updates a Variable under Cell scope"""
		self.setVariable(name, value, AdminControl.getCell(), 'cells')
	
	def setClusterVariable(self, name, value):
		"""Creates or updates a Variable under Cluster scope"""
		for scope, vars in self.vms['clusters'].items():
			self.setVariable(name, value, scope, 'clusters')
		
	def setNodeVariable(self, name, value):
		"""Creates or updates a Variable on every Node"""
		for scope, vars in self.vms['nodes'].items():
			self.setVariable(name, value, scope, 'nodes')
	
	def setServerVariable(self, name, value):
		"""Creates or updates a Variable on every Server"""
		for scope, vars in self.vms['servers'].items():
			self.setVariable(name, value, scope, 'servers')
			
	def getVariableValue(self, _symbolicName, parentConfigId):
		variableSubstitutionEntries = AdminConfig.list('VariableSubstitutionEntry', parentConfigId)
		value = None
		for variableSubstitutionEntry in variableSubstitutionEntries.splitlines():
			symbolicName = AdminConfig.showAttribute(variableSubstitutionEntry, 'symbolicName')
			if (symbolicName == _symbolicName):
				value = AdminConfig.showAttribute(variableSubstitutionEntry, 'value')
		return value	
	
	def unsetVariable(self, name, ignored, scope = None, type = None):
		"""Remove a Variable under the given scope or under all scopes if scope = None"""
		if scope is None or type is None:
			self.__call(self.unsetVariable, name, ignored, scope, type)
		
		if self.vms[type][scope]['vars'].has_key(name):
			AdminConfig.remove( self.vms[type][scope]['vars'][name]['id'] )
			del self.vms[type][scope]['vars'][name]
			print "Variable '%s' removed under scope '%s'." % (name, scope)
			return 1==1
		
		return None

	def unsetCellVariable(self, name):
		"""Removes a Variable under Cell scope"""
		self.unsetVariable(name, None, AdminControl.getCell(), 'cells')
	
	def unsetClusterVariable(self, name):
		"""Removes a Variable under Cluster scope"""
		for scope, vars in self.vms['clusters'].items():
			self.unsetVariable(name, None, scope, 'clusters')
			
	def unsetNodeVariable(self, name):
		"""Removes a Variable on every Node"""
		for scope, vars in self.vms['nodes'].items():
			self.unsetVariable(name, None, scope, 'nodes')
		
	def unsetServerVariable(self, name):
		"""Removes a Variable on every Server"""
		for scope, vars in self.vms['servers'].items():
			self.unsetVariable(name, None, scope, 'servers')

