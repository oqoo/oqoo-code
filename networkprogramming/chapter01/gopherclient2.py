# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Simple Gopher Client
# gopherclient2.py

#命令行运行: python gopherclient2.py guux.org /

import socket, sys

port = 70			 #Gopher uses port 70
host = sys.argv[1]
filename = sys.argv[2]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	s.connect((host, port))
except socket.gaierror, e:
	print "Error connection to server: %s"% e
	sys.exit(1)

#使用文件的读写方式
fd = s.makefile('rw',0)
fd.write(filename + "\r\n")
for line in fd.readlines():
	sys.stdout.write(line)



