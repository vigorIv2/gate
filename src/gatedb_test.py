#!/usr/bin/python
# -*- coding: utf-8 -*-

import gatedb

gdb=gatedb.gatedb()
gdb.get_shapes()
for e in gdb.get_events():
    print e[1]

print gdb.get_events_before("/opt/data/motion/02-20161026030747-01.jpg")

