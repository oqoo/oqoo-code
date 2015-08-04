#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2

f = urllib2.urlopen('http://www.baidu.com')
html = f.read()
print html
