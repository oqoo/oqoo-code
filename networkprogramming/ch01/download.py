#!/usr/bin/env python
# -*- coding: utf-8 -*-

#./download.py http://http.us.debian/ls-lR.gz | gunzip | more

#导入tcp/ip协议模块urllib
import urllib, sys

# urlopen打开sys.argv[1]地址，并创建
f = urllib.urlopen(sys.argv[1])
while 1:
	buf = f.read(2048)
	if not len(buf):
		break
	sys.stdout.write(buf)


