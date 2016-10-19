#!/usr/bin/python

import sys
import subprocess
import json
import time
import os
import logging

logging.basicConfig(filename='/var/log/motion/myshape.log',format='%(asctime)s %(levelname)s %(message)s',level=logging.DEBUG)

def checkgate(mygate_json,image) :
	if ( not os.path.isfile(image) ):
		logging.warn("image file not found "+image)
		return 
	sz = os.path.getsize(image)
	if ( sz == 0L ):
		logging.warn("image file empty, removing "+image)
		os.remove(image)	
		return

	try: 
		with open(mygate_json, 'r') as jsonfile:
			myg=jsonfile.read()
		jmyg=json.loads(myg)
		for l in jmyg["level"]:
			print l
	except Exception, err:
        	logging.exception('Error from throws():')

if ( len(sys.argv) != 3 ):
	print "Uaage: checkgate.py <mygate.json> <image file>" 
	sys.exit(0)

checkgate(sys.argv[1],sys.argv[2])

