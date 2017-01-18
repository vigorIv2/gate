#!/usr/bin/env python

import sys
import gatekeeper

gk=gatekeeper.GateKeeper()

if ( len(sys.argv) < 2 ):
	print "Usage: gatestatus.py [-v] <[-daemon || -check image || -dedupe img || -diff <img1> <img2>> || -dedupe_all || -train img names comma separated>"
	sys.exit(0)

visual=False
for p in sys.argv:
	if p.lower() == "-v":
		visual = True
if sys.argv[1].lower() == "-diff":
	sim=gk.diff_images(sys.argv[2],sys.argv[3])
	print "Similar:", sim
elif sys.argv[1].lower() == "-train":
	gk.snapshot_all(sys.argv[2],visual)
elif sys.argv[1].lower() == "-daemon":
	gk.daemonize()
elif sys.argv[1].lower() == "-check":
	(car,gate)=gk.check_garage_state(sys.argv[2],visual)
	print "car=" + str(car)
	print "gate=" + str(gate)
else:
	print "Unknown arguments "+str(sys.argv)

