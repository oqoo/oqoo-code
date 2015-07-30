#!/usr/bin/env python
# -*- coding: utf-8 -*-

#命令行运行: python server.py
#在另一个命令窗口使用telnet应用程序并连接locakhost的51423端口

import socket

# 主机设置为空字符串，这样程序可以接受来自任意地方的连接
host = ''
port = 51423


# 建立一个socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 设置为可复用的(reusable)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# 绑定端口51423
s.bind((host, port))
# 开始监听来自客户端的请求
s.listen(1)

print "Server is running on port %d; press Ctrl-C to terminate." % port

while 1:
	#连接一个客户端，返回一个新的连接客户端的soket和客户端的ip地址,端口号
	clientsocket, clientaddr = s.accept()
	clientfile = clientsocket.makefile('rw', 0)
	clientfile.write("Welcome, " + str(clientaddr) + "\n")
	clientfile.write("Please enter a string: " )
	line = clientfile.readline().strip()
	clientfile.write("You enterd %d characters.\n" % len(line))
	clientfile.close()
	clientsocket.close()


