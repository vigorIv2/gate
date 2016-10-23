#!/usr/bin/env python

import sys
import subprocess
import json
import time
import os
import logging
import gatekeeper

gk=gatekeeper.GateKeeper()

if ( len(sys.argv) != 2 ):
	print "Uaage: checkgate.py <image file>" 
	sys.exit(0)

gk.checkgate(sys.argv[1])

