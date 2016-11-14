#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging
import json
import time
import sys
#import Image
from PIL import Image
import subprocess
import imutils
import cv2
import gatedb
import re
import datetime

class GateKeeper:
	' base class for GateKeeper software '

	gdb = None
	def __init__(self, ):
		self.gdb=gatedb.gatedb()
		logging.basicConfig(filename='/var/log/motion/gatekeeper.log',format='%(asctime)s %(levelname)s %(message)s',level=logging.DEBUG)

	DEFAULT_DEVIATION = 7 # 5% deviation of area

	# checks that area "a1" is within deviation "d" % from a2
	def within(self,a1,a2,d=DEFAULT_DEVIATION):
		df=(a1*d)/100 # deviation 
		res=( a1 < (a2+df) and a1 > (a2-df) ) # a within deviation range
		return res # a within deviation range
		
	# to find a given shape and area in the array loaded from databse
	def find_shape(self,shapes,shape,area):
		lr=0
		for s in shapes:
			rshape = s[1]
			if ( rshape == u'square' ):
				rshape = u'rectangle' # treat square as rectangles
			if ( rshape == shape ):
				if ( self.within(s[2],area) ):
					return lr
			lr+=1
		return None

	# compares two images and returns a number - if numer too big - imges too different
	def similar_images(self,img1,img2):
		too_different=250000
#		compare -metric AE -fuzz 5% ./test/goco01.jpg ./test/goci02.jpg /dev/null
		image1 = cv2.imread(img1)
		(h1, w1) = image1.shape[:2]
		image2 = cv2.imread(img2)
		(h2, w2) = image2.shape[:2]
		if ( h1 != h2 or w1 != w2 ):
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
		if (h1 != h2 or w1 != w2):
			logging.info("images different? h1=" + str(h1) + " h2=" + str(h2) + " w1=" + str(w1) + " w2=" + str(w2))
			return False
		cmd = ['compare', '-verbose', '-metric', 'MAE', img1, img2, 'null:']
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		diff=0
		for ln in err.split("\n"):
			if ( "all:" in ln ):
				diff=float(ln.lstrip().split(" ")[2].lstrip("(").rstrip(")"))
		logging.info("images different? cmd=" + " ".join(cmd) + " result=" + str(diff))
		return diff < too_different

	def is_acceptable_area(self,A):
		if ( A == None ):
			return False
		MIN_A = 7
		MAX_A = 1500
		return (A >= MIN_A and A <= MAX_A)

	def checkgate(self,image_name,visual_trace = True) :
		if ( not os.path.isfile(image_name) ):
			logging.warn("image file not found "+image_name)
			return
		sz = os.path.getsize(image_name)
		if ( sz == 0L ):
			logging.warn("image file empty, ignoring "+image_name)
			return

		logging.info("processing image_name="+image_name)
		try:
			shapes=self.gdb.get_shapes()
			# load the image and resize it to a smaller factor so that
			# the shapes can be approximated better

			image = cv2.imread(image_name)
			resized = imutils.resize(image, width=300)
			ratio = image.shape[0] / float(resized.shape[0])

			# convert the resized image to grayscale, blur it slightly,
			# and threshold it
			gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (5, 5), 0)
			#thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]
			thresh = cv2.adaptiveThreshold(blurred,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,2)

			# find contours in the thresholded image and initialize the
			# shape detector
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
	
			ML = -1	
			rcnt = 0
			contDet = 0 # number of countours detected
			trying = ""	
			# loop over the contours
			for c in cnts:
				# compute the center of the contour, then detect the name of the
				# shape using only the contour
				M = cv2.moments(c)
				shape = self.detect(c)
				A = M["m00"] # Area
				L = self.find_shape(shapes,shape,A)
				if ( A > 10) :
					contDet += 1
					trying += "s="+shape+ " a="+ str(A)+"; "
				if ( L == None ):
					continue
				if ( L < ML ):
					continue
				ML = L
				rcnt += 1
				logging.info("in file "+image_name+ " recognized shape="+ shape+ " area="+ str(A)+ " level="+ str(L))

				cX = int((M["m10"] / M["m00"]) * ratio)
				cY = int((M["m01"] / M["m00"]) * ratio)

				# multiply the contour (x, y)-coordinates by the resize ratio,
				# then draw the contours and the name of the shape on the image
				c = c.astype("float")
				c *= ratio
				c = c.astype("int")
				cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
				cv2.putText(image, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

				# show the output image
				if ( visual_trace ):
					cv2.imshow("image", image)
					cv2.waitKey(0)
			logging.debug("tried "+trying)

			logging.info("contours detected "+str(contDet)+" shapes recognized "+str(rcnt)+ " shapes expected total "+str(len(shapes)))
			if ( contDet > len(shapes)*3 ): # it usually recognizes lots of shapes
				new_gate_state = rcnt < (len(shapes)*0.66)
				if ( self.gdb.gate_state() == new_gate_state ):
					logging.info("no gate state change detected, it is still open = "+str(new_gate_state))
				else:
					self.gate_state_changed(new_gate_state)
			else:
				logging.debug("Too little contours detected, it is likely because too dark due to gate is closed or night")  
		except Exception, err:
			logging.exception('Error from throws():')

	def crop_image(self,srcimg,destimg,left,upper,width,lower):
		i = Image.open(srcimg)
		w = i.size[0]
		h = i.size[1]

		frame2 = i.crop(((left, upper, width, lower)))
		frame2.save(destimg)

	def reg_file_name(self,fn, id):
		return fn.split(".")[0]+"_"+str(id)+".jpg"

	def snapshot_regions(self,imgn):
		for reg in self.gdb.get_reqions():
			rfn=self.reg_file_name(imgn,reg[0])
			self.crop_image(imgn,rfn,reg[2],reg[3],reg[4],reg[5])
			self.gdb.delete_shapes_regions(reg[0])
			self.save_shapes(rfn,reg[0])
			os.remove(rfn)

	def check_shapes_region(self,imgn,regname):
		reg=self.gdb.get_region(regname)
		rfn=self.reg_file_name(imgn,reg[0])
		self.crop_image(imgn,rfn,reg[1],reg[2],reg[3],reg[4])
		shapes=self.gdb.load_shapes(reg[0])

		res= self.shapes_exist(rfn,shapes)
		logging.info("image="+imgn+" region="+regname+" res="+str(res))
		os.remove(rfn)
		return res

	def shapes_exist(self, image_name, shapes_to_find):
		shapes=self.only_acceptable_contours(self.get_contours(image_name))
		fcnt=1
		for s in shapes_to_find:
			if ( self.find_shape(shapes, s[1],s[2])):
				fcnt += 1
		logging.info("fcnt="+str(fcnt)+" len(shapes_to_find)="+str(len(shapes_to_find)))
		return self.within(len(shapes),fcnt)

	def get_contours(self, image):
		if (not os.path.isfile(image)):
			logging.warn("image file not found " + image)
			return
		sz = os.path.getsize(image)
		if (sz == 0L):
			logging.warn("image file empty, ignoring " + image)
			return
		logging.info("detect_shapes image_name=" + image)
		try:
			# load the image and resize it to a smaller factor so that
			# the shapes can be approximated better

			image = cv2.imread(image)
			resized = imutils.resize(image, width=300)
			ratio = image.shape[0] / float(resized.shape[0])

			# convert the resized image to grayscale, blur it slightly,
			# and threshold it
			gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (5, 5), 0)
			# thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]
			thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

			# find contours in the thresholded image and initialize the
			# shape detector
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts

		except Exception, err:
			logging.exception('Error from throws() in detect_shapes:')
			return None

	def only_acceptable_contours(self,cnts):
		shapes = []
		snum=0
		seen = {}
		for c in cnts:
			# compute the center of the contour, then detect the name of the
			# shape using only the contour
			M = cv2.moments(c)
			shape = self.detect(c)
			A = M["m00"]  # Area

			if (not self.is_acceptable_area(A)):
				continue
			if ( shape == u'square' ):
				shape = u'rectangle' # treat square as rectangles
			skey=shape+"-"+str(A)
			if ( not skey in seen.keys() ):
#				logging.debug("recognized shape=" + shape + " area=" + str(A) )
				shape=(snum,shape,A)
				snum += 1
				shapes.append(shape)
				seen[skey]=1
		res= sorted(shapes, key=lambda x: x[1]+"{0:020.2f}".format(round(x[2],2)))
		return res

	def save_shapes(self, image_name, id):
		try:
			shapes=self.only_acceptable_contours(self.get_contours(image_name))
			for s in shapes:
				self.gdb.save_shapes_regions(s[1],s[2],id)

		except Exception, err:
			logging.exception('Error from throws() in save_shapes:'+err)

	def gate_state_changed(self,new_state):
		logging.info("gate state changed, it is now open = "+str(new_state))
		self.gdb.save_gate_state(new_state)

	def detect(self, c):
		# initialize the shape name and approximate the contour
		shape = "unidentified"
		peri = cv2.arcLength(c, True)
		approx = cv2.approxPolyDP(c, 0.04 * peri, True)

		# if the shape is a triangle, it will have 3 vertices
		if len(approx) == 3:
			shape = "triangle"

		# if the shape has 4 vertices, it is either a square or
		# a rectangle
		elif len(approx) == 4:
			# compute the bounding box of the contour and use the
			# bounding box to compute the aspect ratio
			(x, y, w, h) = cv2.boundingRect(approx)
			ar = w / float(h)

			# a square will have an aspect ratio that is approximately
			# equal to one, otherwise, the shape is a rectangle
			shape = "square" if ar >= 0.95 and ar <= 1.05 else "rectangle"

		# if the shape is a pentagon, it will have 5 vertices
		elif len(approx) == 5:
			shape = "pentagon"

		# otherwise, we assume the shape is a circle
		else:
			shape = "circle"

		# return the name of the shape
		return shape

	def ping6(self, interface, addr):
		# ping6 -c 1 -I eth0 -w 1 ff02::1
		if ( ":" in addr ):
			pingcmd="ping6"
		else:
			pingcmd="ping"  
			addr = addr.split("%")[0]
		print ">> ", pingcmd, " ", addr
		pcmd=[pingcmd, '-c', '1', '-s', '1', '-I', interface, '-w', '1', addr]
		logging.debug(" ".join(pcmd))
		p = subprocess.Popen(pcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()

	def broadcastPing6(self, interface, count):
		# ping6 -c 3 -I eth0 ff02::1
		print "<<broadcast ping6 "
		neighbors = []
		pcmd=['ping6', '-s', '1', '-c', count, '-I', interface, 'ff02::1']
		logging.debug("broadcast "+" ".join(pcmd))
		p = subprocess.Popen(pcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()

		if ( len(err) != 0 ): 
			print "Error in ping6 " , err
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
    # fe80::6203:8ff:fe91:5c56 dev eth0 lladdr 60:03:08:91:5c:56 REACHABLE
    # fe80::76d0:2bff:fecf:1257 dev eth0 lladdr 74:d0:2b:cf:12:57 STALE

		response_json = {}
		pcmd=['ip', 'neigh']
		logging.debug(" ".join(pcmd))
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
			if ( n[cn] == keyl ):
				return n
		return None

	def neighborhood_watch(self,trusted_neighbors):
		num=7
		while True:
			pn=self.gdb.get_neighborhood_state()
			cn=[]
			ns=[]
			if ( (num % 7) == 0 ): 
				neigh=self.broadcastPing6('eth0','1')
			num += 1 
			neighm=self.current_neighbors()
			for n in neighm['neighbors']:
				brand=self.lookup_brand(n['mac'].lower())
				ln=self.lookup_neighbor(trusted_neighbors,n['mac'],2)
				ns.append(n)
				if ( ln != None ):
					print "======= trusted mac ", n, " ",ln[3]," ", brand 
					cn.append(ln[0])
					if ( n['status'] == 'STALE' ):
						self.ping6('eth0', n['ip'])
					else:
						if ( not self.lookup_prev_neighbors(pn,n['status'],ln) ):
							self.new_neighbor(ln)
						self.gdb.save_neighbor_state(n['status'],ln[0])
				else:
					jip=n['ip'].lower().split("%")[0]
					lin=self.lookup_neighbor(trusted_neighbors,n['mac'],2)
					if (lin != None):
						print "======= trusted ip ", n, " ", jin[3]," ", brand
						cn.append(lin[0])
						if ( n['status'] == 'STALE' ):
							self.ping6('eth0', n['ip'])
						else:
							if ( not self.lookup_prev_neighbors(pn,n['status'],lin) ):
								self.new_neighbor(lin)
							self.gdb.save_neighbor_state(n['status'],lin[0])

			print "-=-=-=-=-=-=-=-==-=---=-=--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
			for n in pn:
				if ( not n[0] in cn ):
					self.neighbor_away(n)
					cn.append(n[0]) # so not to drop it again
			time.sleep(1.9)

	def lookup_prev_neighbors(self,pn,st,ln):
		for l in pn:
			if ( l[0] == ln[0] ):
				return True
		return False
	
	def open_gate(self):
		logging.info("Command to open gate")
		
	def close_gate(self):
		logging.info("Command to close gate")
		
	def new_neighbor(self,ln):
		gs=self.gdb.gate_state()
		logging.info("new neighbor "+ str(ln)+" gate state open = "+str(gs))
		if ( gs == False ):
			self.open_gate()
			
	def neighbor_away(self,ln):
		# check to see when status was last updated
		few_min_ago_ts=datetime.datetime.now() - datetime.timedelta(minutes=2)
		few_min_ago=few_min_ago_ts.strftime('%Y-%m-%d %H:%M:%S')
		logging.debug("neighbor went away "+ str(ln)+" min_ago "+few_min_ago)

		if ( few_min_ago > ln[2] ):
			if ( self.gdb.gate_state() ):
				self.close_gate()
			logging.info("newghbor "+str(ln)+" away for too long, deleting neighbor state")
			self.gdb.drop_neighbor_state(ln[0])
			
	def daemonize(self):
		self.neighborhood_watch(self.gdb.get_trusted_neighbors())

	def dedupe(self,cur_fn):
		logging.info("Current file "+cur_fn)
		if (not os.path.exists(cur_fn)):
			self.gdb.delete_file_record(cur_fn)
			return
		for fn in self.gdb.get_files_before(cur_fn):
			if (not os.path.exists(fn)):
				self.gdb.delete_file_record(fn)
				continue
			if ( self.diff_images(cur_fn,fn) ):
				logging.info("Removing file "+fn+" as very similar to current file "+cur_fn)
				os.remove(fn)
				self.gdb.delete_file_record(fn)
			else:
				break


	def dedupe_all(self):
		for e in self.gdb.get_events():
			self.dedupe(e[1])
