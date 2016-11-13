#!/usr/bin/env python

import sys
import gatekeeper

gk=gatekeeper.GateKeeper()

if ( len(sys.argv) < 2 ):
	print "Usage: checkgate.py <[-d] || image file || -e imgname || -c <img1> <img2>> || -da"
	sys.exit(0)

if ( sys.argv[1].lower() == "-c" ):
	sim=gk.diff_images(sys.argv[2],sys.argv[3])
	print "Similar:", sim
elif ( sys.argv[1].lower() == "-e" ):
	gk.dedupe(sys.argv[2])
elif (sys.argv[1].lower() == "-d"):
	gk.daemonize()
elif (sys.argv[1].lower() == "-da"):
	gk.dedupe_all()
else:
	gk.checkgate(sys.argv[1])

