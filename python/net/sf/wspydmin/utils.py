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

import os

from net.sf.wspydmin       import AdminConfig, AdminControl, AdminTask
from net.sf.wspydmin.jvm   import JavaVirtualMachine

#from java.lang                                import String

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

def isManagedServer(serverId): 
    return (serverId.find('servers/ND') != -1) or (serverId.find('/servers/server1') != -1)

def isAdminServer(serverId):
    return (serverId.find('/servers/server1') != -1) or (serverId.find('/servers/dmgr') != -1)

def isServerClustered(serverId):
    """
    Server is clustered if and only if server name is 'dmgr'. Otherwise is non clustered
    """
    return serverId.find('/servers/dmgr') != -1

def isNodeAgentServer(serverId):
    return serverId.find('/servers/nodeagent') != -1

def isWebServer(serverId):
    serverName = serverId.split('/servers/')[1].split('|')[0]
    if ((serverName.find('web') != -1) or (serverName.find('WEB') != -1)):
        return 1
    else:
        return 0

def getServerName(serverId): 
    return serverId.split('/servers/')[1].split('|')[0]
    
def getBusName(busId): 
    return busId.split('/buses/')[1].split('|')[0]    

def getClusterName(clusterId): 
    return clusterId.split('/clusters/')[1].split('|')[0]

def getNodeName(serverId): 
    return serverId.split('nodes/')[1].split('/servers')[0]

def getNodeId(serverId):
    nodeName = getNodeName(serverId)
    nodeList = AdminConfig.list('Node').splitlines()
    nodeId = None
    for node in nodeList:
        if (node.find(nodeName) != -1): 
            nodeId = node
    return nodeId    

def isAdminHost(serverPort): 
    return serverPort.startswith('[WC_adminhost ')

def isAdminHostSecure(serverPort): 
    return serverPort.startswith('[WC_adminhost_secure ')

def isDefaultHost(serverPort): 
    return serverPort.startswith('[WC_defaulthost ')

def getApplicationName(applicationDeploymentId): 
    return applicationDeploymentId.split('deployments/')[1].split('|')[0]

def getPort(serverPort):
    return int(serverPort.split('[port ')[1].split('] [node')[0])

def modifyServerPort(serverName, nodeName, endPointName, newPort):
    print 'About to change server %s endpoint %s to new Port %s' % (serverName, endPointName, newPort)
    opts = '[-nodeName %s -endPointName %s -host * -port %s -modifyShared true]' % (nodeName, endPointName, newPort)
    AdminTask.modifyServerPort(serverName, opts)

def changePorts(servers, endPointPorts):
    for srvId in servers:
        for endPointName, newPort in endPointPorts.items():
            modifyServerPort(getServerName(srvId), getNodeName(srvId), endPointName, newPort)
        
def setClassLoader(appname, mode='PARENT_LAST', policy='SINGLE'):
    print "Setting '%s' application classloader to mode '%s' and warClassLoaderPolicy '%s'" % (appname, mode, policy)
    dep = AdminConfig.getid('/Deployment:%s/' % appname)
    depObject = AdminConfig.showAttribute(dep, 'deployedObject')
    classldr = AdminConfig.showAttribute(depObject, 'classloader')
    #
    AdminConfig.modify(classldr, [['mode', mode]])
    AdminConfig.modify(depObject, [['warClassLoaderPolicy', policy]])

#removes ../ from jar location, as wsadmin run from profile_home/bin
def adjustCurrentPathFromBinProfileDirToRootProfileDir(directory):
    l = String(directory).length()
    endLocation = String(directory).substring(3, l)
    return endLocation    
    
def installSignerCertificateInKeyStore(certFileName, keyStoreName):

    certFileLocation = certFileName
    print 'preparing installation of certificate %s from file %s into store %s' % (certFileName, certFileLocation, keyStoreName)    

    AdminTask.addSignerCertificate(['-keyStoreName', keyStoreName, '-certificateAlias', 'customcert_' + certFileName, '-certificateFilePath', certFileLocation, '-base64Encoded', 'true'])
    
    print 'certificate %s is installed in keystore %s'     % (certFileName, keyStoreName)
    
def deleteCustomSignerCertificatesFromKeyStore(keyStoreName):

    print 'preparing removal of custom certificates from store %s' % (keyStoreName)
        
    certificateList = AdminTask.listSignerCertificates(['-keyStoreName', keyStoreName]).splitlines()
    
    for certificate in certificateList:

        certAlias = certificate.split('] [alias')[1].split('] [validity')[0]

        if (certAlias.find('customcert_') != -1):
            AdminTask.deleteSignerCertificate(['-keyStoreName', keyStoreName, '-certificateAlias', certAlias])    
            print 'certificate %s has been deleted' % (certAlias)
        else:
            print 'certificate %s will not be deleted' % (certAlias)    