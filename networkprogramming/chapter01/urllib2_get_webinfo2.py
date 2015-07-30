#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, urllib2

#urllib2.Request()的功能是构造一个请求信息，返回的req就是一个构造好的请求。

req = urllib2.Request(sys.argv[1])
res = urllib2.urlopen(req)

print "\r\nRetrived %s \r\n" % res.geturl()


# 读取－些额外的信息
info = res.info()
for k, v in info.items():
	print "%s = %s " % (k, v)

#读取res里的html
#html = res.read()
#print html
