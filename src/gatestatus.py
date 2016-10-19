#!/usr/bin/python

import sys
import subprocess
import json
import time
import os
import logging
import gatekeeper

gk=gatekeeper.GateKeeper()

if ( len(sys.argv) != 3 ):
	print "Uaage: checkgate.py <mygate.json> <image file>" 
	sys.exit(0)

gk.checkgate(sys.argv[1],sys.argv[2])

