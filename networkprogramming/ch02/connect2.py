#!/usr/bin/env python
# -*- coding: utf-8 -*-

# [P21] connect2.py
# 寻找端口号
# python的socket库包含一个getservbyname()的函数来查询端口号

import socket

print "Creating socket..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "done."


print "Lokking up port number..."
port = socket.getservbyname('http','tcp')
print "done."

print "Connecting to remote host on port %d..." % port
s.connect(("www.baidu.com", port))
print "done."
