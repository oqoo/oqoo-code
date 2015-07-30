# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Simple Gopher Client
# gopherclient.py

#命令行运行: python gopherclient.py guux.org /

import socket, sys

port = 70			 #Gopher uses port 70
host = sys.argv[1]
filename = sys.argv[2]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	s.connect((host, port))
	fd = s.makefile('rw',0)
except socket.gaierror, e:
	print "Error connection to server: %s"% e
	sys.exit(1)

s.sendall(filename + "\r\n")

while 1:
	buf = s.recv(2048)
	if not len(buf):
		break
	sys.stdout.write(buf)
