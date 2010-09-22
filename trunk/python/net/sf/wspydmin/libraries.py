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

from java.lang                     import IllegalArgumentException, IllegalStateException

from net.sf.wspydmin               import AdminConfig, AdminControl
from net.sf.wspydmin.admin         import Cell
from net.sf.wspydmin.resources     import Resource
from net.sf.wspydmin.classloaders  import ClassLoader

class Library(Resource):
	DEF_ID    = '/Library:%(name)s/'
	DEF_ATTRS = {
               'name' : None,
          'classPath' : None,
         'nativePath' : None,
        'description' : None
	}
	
	__NAMEPREFIX__ = 'WSPYDMINLIB_'
	
	def __init__(self, name, parent = Cell()):
		Resource.__init__(self)
		self.name   = Library.__NAMEPREFIX__ + str(name)
		self.parent = parent
		
		self.__classpath   = []
		self.__nativepath  = []
		self.__libraryRefs = []
	
	def __create__(self, update):
		if self.classPath is None:
			self.classPath = String(str(self.__classpath)[2:-2]).replaceAll("', '", ';')
		
		if self.nativePath is None:
			self.nativePath = String(str(self.__nativepath)[2:-2]).replaceAll("', '", ';')
		
		Resource.__create__(self, update)
		
		for libRef in self.__libraryRefs:
			libRef.__create__(update)
	
	def addClassPathEntry(self, classPathEntry):
		self.__classpath.append(classPathEntry)
	
	def addLibraryRef(self, targetResourceName):
		self.__libraryRefs.append(LibraryRef(self, targetResourceName))
	
	def addNativePathEntry(self, nativePathEntry):
		self.__nativepath.append(nativePathEntry)
	
	def remove(self):
		for librefId in AdminConfig.list('LibraryRef').splitlines():
			libName = AdminConfig.showAttribute(librefId, 'libraryName')
			if self.name == libName:
				AdminConfig.remove(librefId)
		Resource.remove(self)
	
	def removeAll(self):
		map(
			lambda x: Library(x).remove(), # remove library by given name
			map(
				lambda x: x.split('(')[0].split(Library.__NAMEPREFIX__)[1], # get library name from ID 
				filter( 
					lambda x: x.startswith(Library.__NAMEPREFIX__), # get only custom libraries
					AdminConfig.list(self.__wastype__).splitlines()
				)
			)
		)

class LibraryRef(Resource):
	DEF_ID    = '/LibraryRef:/'
	DEF_ATTRS = {
              'libraryName' : None,                          
        'sharedClassloader' : None
	}
	
	def __init__(self, library, targetResourceName):
		self.__wassuper__()
		self.libraryName        = library.name
		self.targetResourceName = targetResourceName
		
		#TODO implement libraryRef on Server with the right classloading mode later with targetResourceType='Server'
		if ((targetResourceName is None) or (targetResourceName == '')):
			raise IllegalArgumentException, 'Cannot create a library Ref on a (server or application) with no name'
		self.parent = ClassLoader(targetResourceName)
	
	def __postinit__(self):	
		self.__wassuper__.__postinit__()
		if (self.__scope__ is None):   # <-- scope = parent.__id__
			raise IllegalStateException, 'Cannot create a library Ref on a (server or application) that does not exist'
	
	def __getconfigid__(self):
		for librefId in AdminConfig.list(self.__wastype__).splitlines():
			libName = AdminConfig.showAttribute(librefId, 'libraryName')
			if (libName == self.libraryName and librefId.find(self.targetResourceName)!=-1 ):
				return librefId
		return None

