# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Simple Gopher Client

# [P10] gopherclient.py
# 命令行运行: python gopherclient.py
# 示例处理Gopher协议, Gopher协议是在Web出现之前的一种非常流行的协议

import socket, sys

port = 70			 #Gopher 协议使用70作为端口号
host = 'guux.org'	 #Gopher协议的的web网站
filename = '/'		 #目录路径

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	s.connect((host, port))
except socket.gaierror, e:
	print "Error connection to server: %s"% e
	sys.exit(1)

s.sendall(filename + "\r\n")

while 1:
	buf = s.recv(2048)
	if not len(buf):
		break
	sys.stdout.write(buf)
