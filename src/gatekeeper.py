#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging
import json
import time
import subprocess
import imutils
import cv2
import gatedb
import re
import datetime
from os import listdir
from os.path import isfile, join

class GateKeeper:
	' base class for GateKeeper software '

	pictures_path='/opt/data/motion'

	gdb = None

	def __init__(self, ):
		self.gdb=gatedb.gatedb()
		self.interface='wlan0'
		logging.basicConfig(filename='/var/log/motion/gatekeeper.log',format='%(asctime)s %(levelname)s %(message)s',level=logging.DEBUG)

	DEFAULT_DEVIATION = 14 # % deviation of area

	def expire(self):
		few_days_ago_ts=datetime.datetime.now() - datetime.timedelta(days=5)
		few_days_ago=few_days_ago_ts.strftime('%Y-%m-%d %H:%M:%S')
		logging.debug("cleaning events older than "+few_days_ago)

		evts=self.gdb.load_events(few_days_ago)
		for e in evts:
			if os.path.exists(e.filename):
				os.remove(e.filename)
				logging.info("Removed expired file "+ e.filename)
		self.gdb.drop_events(few_days_ago)
		now_ts=datetime.datetime.now()
		now=now_ts.strftime('%Y-%m-%d %H:%M:%S')
		evts2=self.gdb.load_events(now)
		for e in evts2:
			if not os.path.exists(e.filename):
				logging.info("Removing record about missing file "+ e.filename)
				self.gdb.drop_event(e.id)

		self.drop_orphans()

	def drop_orphans(self):
		onlyfiles = [f for f in listdir(self.pictures_path) if isfile(join(self.pictures_path, f))]
		for f in onlyfiles:
			p = self.pictures_path + "/" + f
			if not self.gdb.is_registered(p):
				logging.info("removing orphan "+p)
				os.remove(p)

	def push_button(self):
		logging.info("push_button begin")
		return
		import RPi.GPIO as GPIO ## Import GPIO library

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		pin=7
		GPIO.setup(pin, GPIO.OUT)
		GPIO.output(pin,False)
		time.sleep(4)
		GPIO.output(pin,True)
		logging.info("push_button end")

	# checks that area "a1" is within deviation "d" % from a2
	def within(self, a1, a2, d=DEFAULT_DEVIATION):
		df=(a1*d)/100 # deviation
		a2pdf=a2+df
		a2mdf=a2-df
		res=a1 < a2pdf and a1 > a2mdf # a within deviation range
		return res # a within deviation range

	# compares two images and returns a number - if numer too big - imges too different
	def similar_images(self,img1,img2):
		too_different=250000
#		compare -metric AE -fuzz 5% ./test/goco01.jpg ./test/goci02.jpg /dev/null
		image1 = cv2.imread(img1)
		(h1, w1) = image1.shape[:2]
		image2 = cv2.imread(img2)
		(h2, w2) = image2.shape[:2]
		if h1 != h2 or w1 != w2:
			logging.info("images similar? h1="+ str(h1)+" h2="+str(h2)+" w1="+str(w1)+" w2="+str(w2))
			return False
		cmd=['compare', '-metric', 'AE', '-fuzz', '5%', img1, img2, '/dev/null']
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		diff=int("".join(err))
		logging.info("images similar? cmd="+ " ".join(cmd)+ " result="+ str(diff))
		return diff < too_different

	# compares two images and returns a number - if numer too big - imges too different
	def diff_images(self, img1, img2):
		too_different = 0.05
		# compare - verbose - metric MAE 15.jpg 00.jpg null:
		image1 = cv2.imread(img1)
		(h1, w1) = image1.shape[:2]
		image2 = cv2.imread(img2)
		(h2, w2) = image2.shape[:2]
		if h1 != h2 or w1 != w2:
			logging.info("images different? h1=" + str(h1) + " h2=" + str(h2) + " w1=" + str(w1) + " w2=" + str(w2))
			return False
		cmd = ['compare', '-verbose', '-metric', 'MAE', img1, img2, 'null:']
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		diff=0
		for ln in err.split("\n"):
			if "all:" in ln:
				diff=float(ln.lstrip().split(" ")[2].lstrip("(").rstrip(")"))
		logging.info("images different? cmd=" + " ".join(cmd) + " result=" + str(diff))
		return diff < too_different

	def is_acceptable_feature(self,A,vertices):
		if A == None or A == 0: # ignore zero area
			return False
		if vertices == 2: # ignore lines
			return False
		if not vertices in (3,5,8,7): # wrong shape - ignore
			return False
		MIN_A = 60
		MAX_A = 800
		return A >= MIN_A and A <= MAX_A

	def patch_region(self,reg,algo):
		return reg[0],reg[1],reg[2],reg[3],reg[4],reg[5],algo

	def snapshot_all(self,imgnms,visual):
		reg=self.gdb.get_region("all")
		cnts = self.get_contours(imgnms, reg)
		shapes = self.get_features(cnts,imgnms,reg,visual)
		(coveredByCar, clearGate) = self.split_shapes(shapes,visual)
		if coveredByCar == None or len(coveredByCar) < 3:
			msg="Not enough shapes covered by car detected"
			print msg
			logging.error(msg)
			return

		if clearGate == None or len(clearGate) < 3:
			msg="Not enough shapes on gate detected"
			print msg
			logging.error(msg)
			return

		self.gdb.delete_features(reg.id)

		self.save_features(coveredByCar,reg,True)
		self.save_features(clearGate,reg,False)
		self.gdb.close()

	def check_features(self,imgn,regname,visual):
		reg=self.gdb.get_region(regname)
		shapes=self.gdb.load_features(reg.id)
		shapesCoveredByCar = filter(lambda x: x.coveredByCar == 1, shapes)
		shapesGate = filter(lambda x: x.coveredByCar == 0, shapes)

		(resCar0, cnt1)= self.shapes_exist(imgn,reg,shapesCoveredByCar,visual)
		resCar=not resCar0
		logging.info("image="+imgn+" region="+regname+" resCar="+str(resCar)+" cnt="+str(cnt1))
		(resGate,cnt2)= self.shapes_exist(imgn,reg,shapesGate,visual)
		logging.info("image="+imgn+" region="+regname+" resGate="+str(resGate)+" cnt="+str(cnt2))
		return resCar,resGate,cnt1+cnt2

	def shapes_exist(self, image_name, reg, shapes_to_find, visual):
		cnts=self.get_contours(image_name, reg)
		shapes=self.get_features(cnts, image_name, reg, visual, known=shapes_to_find)
		fcnt=len(shapes)
		logging.info("fcnt="+str(fcnt)+" len(shapes_to_find)="+str(len(shapes_to_find)))
		return len(shapes_to_find) == fcnt, fcnt

	def reveal_contours(self,img,reg):
		algo=reg.algorithm
		img = self.read_region(img,reg)
		if algo == 2:
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.adaptiveThreshold(blurred, 255, cv2.CALIB_CB_ADAPTIVE_THRESH, cv2.THRESH_BINARY_INV, 11, 2)
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		if algo == 3:
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.adaptiveThreshold(blurred, 128, cv2.CALIB_CB_ADAPTIVE_THRESH, cv2.THRESH_BINARY_INV, 11, 2)
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		elif algo == 4:
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.threshold(blurred, 55, 255, cv2.THRESH_BINARY_INV)[1]
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) #  NONE) # APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		elif algo == 5:
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.threshold(blurred, 55, 255, cv2.THRESH_BINARY_INV)[1]
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # NONE) # APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		elif algo == 1:
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.threshold(blurred, 55, 255, cv2.THRESH_BINARY_INV)[1]
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)  # NONE) # APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		else:
			return None

	def check_garage_state_regions(self,img,visual):
		(car,fcnt)=self.check_features(img, "car", visual)
		if fcnt > 0:
			if self.gdb.car() != car:
				self.gdb.save_car(car)
		(gate,fcnt)=self.check_features(img, "gate", visual)
		if fcnt > 0:
			if self.gdb.gate() != gate:
				self.gdb.save_gate(gate)
		return car,gate

	def check_garage_state(self,img,visual):
		(car, gate, fcnt)=self.check_features(img, "all", visual)
		if not gate:
			car = None
		else:
			if fcnt > 0:
				if self.gdb.gate() != gate:
					self.gdb.save_gate(gate)
				if self.gdb.car() != car:
					self.gdb.save_car(car)

		self.gdb.close()
		return car, gate

	def get_contours(self, image, reg):
		if not os.path.isfile(image):
			logging.warn("image file not found " + image)
			return None
		sz = os.path.getsize(image)
		if sz == 0L:
			logging.warn("image file empty, ignoring " + image)
			return None
		logging.info("detect_shapes image_name=" + image)
		cnts = self.reveal_contours(image,reg)
		return cnts

	def read_region(self,imgn,reg):
		img = cv2.imread(imgn)
		cropped = img[reg.left:reg.right, reg.upper:reg.lower]
		return cropped

	def is_known_feature(self, f, kk):
		for k in kk:
			res = 0
			if f[2] == k.vertices:
				res += 1
			if self.within(f[1], k.area, 20 ): res += 1
			if self.within(f[3], k.cx, 20 ): res += 1
			if self.within(f[4], k.cy, 20 ): res += 1
			if res == 4:
				return True
		return False

	def get_features(self, cnts, img_nme, reg, visual, known=None):
		if cnts is None:
			return []
		snum=0
		ratio=1
		img = self.read_region(img_nme, reg)
		sumY=0
		numY=0
		for c in cnts:
			# compute the center of the contour, then detect the name of the
			# shape using only the contour
			M = cv2.moments(c)
			(vertices) = self.detect_shape(c)
			A = M["m00"]  # Area
			if not self.is_acceptable_feature(A, vertices):
				continue

			cX = int((M["m10"] / M["m00"]) * ratio)
			cY = int((M["m01"] / M["m00"]) * ratio)
			sumY+=cY
			numY+=1
			avgY=sumY/numY
			devY=float(cY - avgY) / avgY

			shape=(snum,A,vertices,cX,cY)
			if abs(devY) > 0.09: # exclude this one, it is too far below or above the line of known shapes
				sumY -= cY
				numY -= 1
				avgY = sumY / numY
				continue

			snum += 1

			msg="preliminary detection file" + img_nme + " vertices=" + str(vertices) + " area=" + str(A)+" cX="+str(cX)+" cY="+str(cY)+" avgY="+str(avgY)+" devY={0:.4f}".format(round(devY,2))
			logging.info(msg)

			if visual:
				cv2.drawContours(img, [c], -1, (255, 0, 0), 1)

				# show the output image
				cv2.imshow("image", img)
				cv2.waitKey(0)

		shapes = []
		for c in cnts:
			# compute the center of the contour, then detect the name of the
			# shape using only the contour
			M = cv2.moments(c)
			(vertices) = self.detect_shape(c)
			A = M["m00"]  # Area
			if A <= 0:
				continue

			cX = int((M["m10"] / M["m00"]) * ratio)
			cY = int((M["m01"] / M["m00"]) * ratio)
			devY = float(cY - avgY) / avgY

			shape = (snum, A, vertices, cX, cY)
			if not self.is_acceptable_feature(A, vertices):
				continue

			# logging.debug("recognized shape=" + shape + " area=" + str(A) )
			snum += 1
			if known is None:
				if abs(devY) > 0.04:  # exclude this one, it is too far below or above the line of known shapes
					continue
			else:
				if not self.is_known_feature(shape,known):
					continue
			shapes.append(shape)

			msg = "final detection file" + img_nme + " vertices=" + str(vertices) + " area=" + str(A) + " cX=" + str(cX) + " cY=" + str(cY) + " avgY=" + str(avgY) + " devY={0:.4f}".format(round(devY,2))
			logging.info(msg)

			if visual:
 				cv2.drawContours(img, [c], -1, (0, 255, 0), 2)

				# show the output image
				cv2.imshow("image", img)
				cv2.waitKey(0)
		return shapes

	def split_shapes(self,shapes,visual):
		res=sorted(shapes, key=lambda x: "{0:020.2f}".format(round(x[3],2)))
		covered=res[:3]
		clear=res[3:]
		if visual:
			for r in covered:
				print "covered res1="+str(r)
			for r in clear:
				print "clear res2=" + str(r)
		return covered, clear

	def save_features(self, shapes, reg, coveredByCar):
		for s in shapes:
			self.gdb.save_feature(s[1],s[2],s[3],s[4],coveredByCar,reg.id)

	def gate_state_changed(self,new_state):
		logging.info("gate state changed, it is now open = "+str(new_state))
		self.gdb.save_gate(new_state)

	def detect_shape(self, c):
		peri = cv2.arcLength(c, True)
		approx = cv2.approxPolyDP(c, 0.04 * peri, True)
		return (len(approx))

	def ping6(self, interface, addr):
		# ping6 -c 1 -I wlan0 -w 1 ff02::1
		if ":" in addr:
			pingcmd="ping6"
		else:
			pingcmd="ping"  
			addr = addr.split("%")[0]
		pcmd=[pingcmd, '-c', '1', '-s', '1', '-I', interface, '-w', '1', addr]
		logging.debug(" ".join(pcmd))
		p = subprocess.Popen(pcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()

	def broadcastPing6(self, interface, count):
		# ping6 -c 3 -I wlan0 ff02::1
		print "<<broadcast ping6 "
		neighbors = []
		pcmd=['ping6', '-s', '1', '-c', count, '-I', interface, 'ff02::1']
		logging.debug("broadcast "+" ".join(pcmd))
		p = subprocess.Popen(pcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()

		if len(err) != 0:
			print "Error in ping6 ", err
			return 
		for l in out.split("\n"):
			ls=l.split(" ") 
			if ( l == "" or ls < 2 ):
				break # end of ping6 command output, further just stats, ignore that
			if ( ls[0] != 'PING' ):
				neighbors.append("%".join([ls[3].rstrip(':'),interface]))

		return neighbors

	def current_neighbors(self):
		# ip neigh
    # fe80::6203:8ff:fe91:5c56 dev wlan0 lladdr 60:03:08:91:5c:56 REACHABLE
    # fe80::76d0:2bff:fecf:1257 dev wlan0 lladdr 74:d0:2b:cf:12:57 STALE

		response_json = {}
		pcmd=['ip', 'neigh']
#		logging.debug(" ".join(pcmd))
		p = subprocess.Popen(pcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()

		if ( len(err) != 0 ):
			logging.error("Error in IP " +str(err))
			return
		mac_pattern = re.compile("^([A-Fa-f0-9\:]+)*$")
		macs=[]
		for l in out.split("\n"):
			ls=l.split(" ")
			if ( l == "" or ls < 5 ):
				break # end of ip command output, ignore rest
			if ( mac_pattern.match(ls[4])):
				macs.append({"mac" : ls[4], "status" : ls[5], "ip" : "%".join([ls[0],ls[2]])})

		response_json["neighbors"] = macs
		return response_json

	def lookup_brand(self,mac):
		return self.gdb.oui_vendor(mac.lower()[:8])

	def lookup_neighbor(self,neighbors,key,cn):
		keyl=key.lower()
		for n in neighbors:
			if ( n.mac == keyl ):
				return n
		return None

	def neighborhood_watch(self,trusted_neighbors):
		num=7
		while True:
			if self.gdb is None:
				self.gdb = gatedb.gatedb()
			pn=self.gdb.get_neighborhood_state()
			cn=[]
			ns=[]
			if ( (num % 7) == 0 ): 
				neigh=self.broadcastPing6(self.interface,'1')
			num += 1 
			neighm=self.current_neighbors()
			for n in neighm['neighbors']:
#				brand=self.lookup_brand(n['mac'].lower())
				ln=self.lookup_neighbor(trusted_neighbors,n['mac'],2)
				ns.append(n)
				if ( ln != None ):
					print "======= trusted mac ", n, ln.name 
					cn.append(ln.id)
					if ( n['status'] == 'STALE' ):
						self.ping6(self.interface, n['ip'])
					if ( not self.lookup_prev_neighbors(pn,n['status'],ln) ):
						self.new_neighbor(ln)
					self.gdb.save_neighbor_state(n['status'],ln.id)
				else:
					jip=n['ip'].lower().split("%")[0]
					lin=self.lookup_neighbor(trusted_neighbors,n['mac'],2)
					if (lin != None):
						print "======= trusted ip ", n, jip.name
						cn.append(lin[0])
						if ( n['status'] == 'STALE' ):
							self.ping6(self.interface, n['ip'])
						if ( not self.lookup_prev_neighbors(pn,n['status'],lin) ):
							self.new_neighbor(lin)
						self.gdb.save_neighbor_state(n['status'],lin.id)

			for n in pn:
				if ( not n.id in cn ):
					self.neighbor_away(n)
					cn.append(n.id) # so not to drop it again
			self.gdb.close()
			time.sleep(1.9)

	def lookup_prev_neighbors(self,pn,st,ln):
		for l in pn:
			if ( l.id == ln.id ):
				return True
		return False
	
	def open_gate(self):
		logging.info("Command to open gate")
		self.push_button()

	def close_gate(self):
		logging.info("Command to close gate")
		self.push_button()
		
	def new_neighbor(self,ln):
		gate=self.gdb.gate()
		car=self.gdb.car()
		logging.info("new neighbor "+ str(ln)+" gate state closed = "+str(gate)+" car = "+str(car))
		if ( gate == True and car == False ):
			self.open_gate()
			
	def neighbor_away(self,ln):
		# check to see when status was last updated
		few_min_ago_ts=datetime.datetime.now() - datetime.timedelta(minutes=1)
		few_min_ago=few_min_ago_ts.strftime('%Y-%m-%d %H:%M:%S')
		logging.debug("neighbor went away "+ str(ln)+" min_ago "+few_min_ago)

		if ( few_min_ago > str(ln.ts) ):
			if ( self.gdb.gate() == False ):
				self.close_gate()
			logging.info("newghbor "+str(ln)+" away for too long, deleting neighbor state")
			self.gdb.drop_neighbor_state(ln.neighbor_id)
			
	def daemonize(self):
		self.neighborhood_watch(self.gdb.get_trusted_neighbors())


