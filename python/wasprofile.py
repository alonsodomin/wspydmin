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

import sys, os, glob

wsPydminLib = os.environ.get('WSPYDMIN_LIB')
if wsPydminLib is None:
	print "ERROR: Environment variable 'WSPYDMIN_LIB' must be set."
	sys.exit(2)

# Load into system path WSPydmin library
print "WSPydmin scripting library installed in: '%s'" % wsPydminLib
sys.path.append(wsPydminLib)

# Load external includes into system path
wsPydminInclude = os.environ.get('WSPYDMIN_INCLUDE')
if not wsPydminInclude is not None:
	for include in glob.glob("%s/python/*" % wsPydminInclude):
		print "WSPydmin has included library found at '%s'" % include
		sys.path.append(include)

# Directly place references to each
# WebSphere admin instance into
# python's table of loaded modules.

sys.modules['AdminApp']     = AdminApp
sys.modules['AdminConfig']  = AdminConfig
sys.modules['AdminControl'] = AdminControl
sys.modules['AdminTask']    = AdminTask
sys.modules['Help']         = Help