#!/usr/bin/env python

import sys
import gatekeeper

gk=gatekeeper.GateKeeper()

if ( len(sys.argv) < 2 ):
	print "Uaage: checkgate.py <[-d] || image file || -c <img1> <img2>>" 
	sys.exit(0)

if ( sys.argv[1].lower() == "-c" ):
	sim=gk.similar_images(sys.argv[2],sys.argv[3])
	print "Similar:", sim
else:
	if ( sys.argv[1].lower() == "-d" ):
		gk.daemonize()
	else:
		gk.checkgate(sys.argv[1])

