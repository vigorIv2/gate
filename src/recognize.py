#!/usr/bin/python

import sys
import subprocess
import json
import time
import os
import logging
import memcache
import RPi.GPIO as GPIO ## Import GPIO library

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

alpr_path="/usr/bin/alpr"

logging.basicConfig(filename='/var/log/motion/recognize.log',format='%(asctime)s %(levelname)s %(message)s',level=logging.DEBUG)

def add_category(fpath,category):
	fpv = fpath.split("/")
 	result="/".join(fpv[:-1])+"/"+category+"/"+fpv[-1]
	return result

def push_button():
	logging.info("push_button begin")
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	pin=7
	GPIO.setup(pin, GPIO.OUT)
	GPIO.output(pin,False)
	time.sleep(4)
	GPIO.output(pin,True)
	logging.info("push_button end")
 	 
def categorize_plate(category_json,image) :
	if ( not os.path.isfile(image) ):
		logging.warn("file not found "+image)
		return 
	sz = os.path.getsize(image)
	if ( sz == 0L ):
		logging.warn("file empty, removing "+image)
		os.remove(image)	
		return
	try: 
		with open(category_json, 'r') as jsonfile:
			cat=jsonfile.read()
		jcat=json.loads(cat)
		jcats=jcat["categories"]
		# do this once for one root image path, create directory structure
		ripp="/".join(image.split("/")[:-1])
  		rid=mc.get("create_image_dirs"+ripp)
		if ( not rid ):
			for cn in [ "low_confidence", "match", "mismatch", "no_plate" ]:
				image_path=add_category(image,jcats[cn])
				image_path="/".join(image_path.split("/")[:-1])
				logging.info("making sure directory "+image_path+" created")
				if (not os.path.exists(image_path)):
					os.makedirs(image_path)
	  		mc.set("create_image_dirs"+ripp,1)

		p = subprocess.Popen([alpr_path, '-c', 'us', '-j', image], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		j = json.loads(out)

		if ( len(j['results']) >= 1 ):
			for r in j['results']:
				plate = r['plate'].encode("utf-8")
				recognized_before = mc.get(plate)
				if ( recognized_before ): # check to see if it was recognized recently, then ignore, delete image
					tdiff = time.time() - recognized_before
					sdiff = "%.2f" % tdiff
					if ( tdiff < 20 ):
						logging.info("plate "+plate+" were recognized "+sdiff+" seconds ago, removing "+image)
						mc.set(plate,time.time())
						os.remove(image)
					else:
						recognized_before = None
						logging.info("plate "+plate+" were recognized "+sdiff+" seconds ago, processing "+image)
						mc.delete(plate)
				if ( not recognized_before ):
					confidence = r['confidence']
					sconf="%.2f" % confidence
					if ( confidence < 80 ):
						logging.info("confidence "+sconf+" too low, moving to removed "+image)
						os.rename(image,add_category(image,jcats["low_confidence"]))
					else:
						mc.set(plate,time.time())
						if ( plate in jcat['allowed_plates'] ):
							logging.info("license plate "+plate+" recognized as allowed with confidence "+sconf+" image="+image)
							push_button()	
							os.rename(image,add_category(image,jcats["match"]))
							with open(add_category(image+".json",jcats["match"]), "w") as json_file:
								json_file.write(out)
						else:
							logging.info("license plate "+plate+" recognized as denied with confidence "+sconf+" image="+image)
							os.rename(image,add_category(image,jcats["mismatch"]))
							with open(add_category(image+".json",jcats["mismatch"]), "w") as json_file:
								json_file.write(out)
		else:
			logging.info("no license plate recognized, moving to removed "+image)
			os.rename(image,add_category(image,jcats["no_plate"]))
	except Exception, err:
        	logging.exception('Error from throws():')
#		print sys.exc_info()
#		logging.info("exception removing image "+image)
#		if ( os.path.isfile(image) ): 
#			os.remove(image)	

if ( len(sys.argv) != 3 ):
	print "Uaage: recognize_plate.py <category_definition.json> <image file name>" 
	sys.exit(0)

categorize_plate(sys.argv[1],sys.argv[2])

