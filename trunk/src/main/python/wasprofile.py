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

import sys, os, glob
wsPydminHome = os.environ.get('WSPYDMIN_HOME')
if wsPydminHome is None:
	print "ERROR: Environment variable 'WSPYDMIN_HOME' must be set."
	sys.exit(2)

wsPydminLib = os.environ.get('WSPYDMIN_LIB')
if wsPydminLib is None:
	print "ERROR: Environment variable 'WSPYDMIN_LIB' must be set."
	sys.exit(2)

# Load into system path WSPydmin library
print "WSPydmin scripting library installed in: '%s'" % wsPydminLib
sys.path.append(wsPydminLib)

# Load external includes into system path
wsPydminInclude = os.environ.get('WSPYDMIN_INCLUDE')
if not wsPydminInclude is None:
	print "WSPydmin has included path at '%s/python'" % wsPydminInclude
	sys.path.append('%s/python' % wsPydminInclude)

scriptHome = os.environ.get('SCRIPT_HOME')
if not scriptHome is None:
    sys.path.append(scriptHome)

# Directly place references to each
# WebSphere admin instance into
# python's table of loaded modules.

sys.modules['AdminApp']     = AdminApp
sys.modules['AdminConfig']  = AdminConfig
sys.modules['AdminControl'] = AdminControl
try:
	sys.modules['AdminTask']    = AdminTask
except :
	sys.modules['AdminTask']    = None
sys.modules['Help']         = Help

# Initialize logging configuration
import logging
logging.basicConfig(filename = '%s/logs/wspydmin.out' % wsPydminHome, level = logging.DEBUG)
