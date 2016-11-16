#!/usr/bin/env python

import sys
import gatekeeper

gk=gatekeeper.GateKeeper()

if ( len(sys.argv) < 2 ):
	print "Usage: gatestatus.py <[-daemon || -check image || -dedupe img || -diff <img1> <img2>> || -dedupe_all || -train img>"
	sys.exit(0)

if ( sys.argv[1].lower() == "-diff" ):
	sim=gk.diff_images(sys.argv[2],sys.argv[3])
	print "Similar:", sim
elif ( sys.argv[1].lower() == "-dedupe" ):
	gk.dedupe(sys.argv[2])
elif (sys.argv[1].lower() == "-train"):
	gk.snapshot_regions(sys.argv[2])
	print "car="+str(gk.check_shapes_region(sys.argv[2], "car"))
	print "gate="+str(gk.check_shapes_region(sys.argv[2],"gate"))
elif (sys.argv[1].lower() == "-daemon"):
	gk.daemonize()
elif (sys.argv[1].lower() == "-dedupe_all"):
	gk.dedupe_all()
elif (sys.argv[1].lower() == "-check"):
	print "car=" + str(gk.check_shapes_region(sys.argv[2], "car"))
 	print "gate=" + str(gk.check_shapes_region(sys.argv[2], "gate"))
#	gk.dedupe(sys.argv[2])
else:
	print "Unknown arguments "+str(sys.argv)

