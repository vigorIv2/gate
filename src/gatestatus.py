#!/usr/bin/env python

import sys
import gatekeeper

gk=gatekeeper.GateKeeper()

if ( len(sys.argv) != 2 ):
	print "Uaage: checkgate.py <[-d] || image file>" 
	sys.exit(0)

if ( sys.argv[1].lower() == "-d" ):
	gk.daemonize()
else:
	gk.checkgate(sys.argv[1])

