#!/usr/bin/env python
# -*- coding: utf-8 -*-

# [P22] connect3.py
# 从socket获取信息

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

#从socket获取信息　
#获取本地的IP地址和端口号(本地端口号是随机生成)
print "Connect from", s.getsockname()
#获取远程机器的IP和端口号
print "Connect to", s.getpeername()

