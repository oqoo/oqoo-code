#!/usr/bin/env python
# -*- coding: utf-8 -*-
# [P20] connect.py

import socket

print "Creating socket..."
#通信类型AF_INET与IPv4对应
#通信家族SOCK_STREAM
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "done."

print "Connection to remote host..."
s.connect(("www.baidu.com",80))

print "done."
