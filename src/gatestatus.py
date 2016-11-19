#!/usr/bin/env python

import sys
import gatekeeper

gk=gatekeeper.GateKeeper()

if ( len(sys.argv) < 2 ):
	print "Usage: gatestatus.py [-v] <[-daemon || -check image || -dedupe img || -diff <img1> <img2>> || -dedupe_all || -train img names comma separated>"
	sys.exit(0)

visual=False
for p in sys.argv:
	if ( p.lower() == "-v" ):
		visual = True
if ( sys.argv[1].lower() == "-diff" ):
	sim=gk.diff_images(sys.argv[2],sys.argv[3])
	print "Similar:", sim
elif ( sys.argv[1].lower() == "-dedupe" ):
	gk.dedupe(sys.argv[2])
elif (sys.argv[1].lower() == "-train"):
	gk.snapshot_regions(sys.argv[2],visual)
#	print "car="+str(gk.check_features(sys.argv[2], "car",visual))
#	print "gate="+str(gk.check_features(sys.argv[2],"gate",visual))
elif (sys.argv[1].lower() == "-daemon"):
	gk.daemonize()
elif (sys.argv[1].lower() == "-dedupe_all"):
	gk.dedupe_all()
elif (sys.argv[1].lower() == "-check"):
	print "car=" + str(gk.check_features(sys.argv[2], "car",visual))
 	print "gate=" + str(gk.check_features(sys.argv[2], "gate",visual))
#	gk.dedupe(sys.argv[2])
else:
	print "Unknown arguments "+str(sys.argv)

