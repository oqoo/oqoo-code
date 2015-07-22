# -*- coding: utf-8 -*-

import xmlrpclib 

class RPCUtil:
    UID=1  #用户名admin所对应的id号 
    PWD="12345"   #admin对应的密码
    DB="BJC20150428"
    PORT="8069"
    URL = "http://10.100.254.168:8069/xmlrpc/object" 
    
    @staticmethod
    def getProxy(): 
        return xmlrpclib.ServerProxy(RPCUtil.URL, allow_none=True)
