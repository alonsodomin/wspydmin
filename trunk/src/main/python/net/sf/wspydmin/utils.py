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

import os

from java.lang                                import String

def str2Array(x):
    if x.startswith('['): # array!
        arr = []
        for val in x[1:-1].split():
            arr.append(str2Array(val))
        return arr
    else:
        return x
        
def splitAttrs(x):
    return [ x.split()[0][1:], str2Array(x.split()[1][:-1]) ]


#removes ../ from jar location, as wsadmin run from profile_home/bin
def adjustCurrentPathFromBinProfileDirToRootProfileDir(directory):
    l = String(directory).length()
    endLocation = String(directory).substring(3, l)
    return endLocation    
