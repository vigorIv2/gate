#!/usr/bin/python
# -*- coding: utf-8 -*-

import gatedb

gdb=gatedb.gatedb()

print gdb.get_events_before("/opt/data/motion/02-20161026030747-01.jpg")

