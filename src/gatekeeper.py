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

class GateKeeper:
	' base class for GateKeeper software '

	gdb = None
	def __init__(self, ):
		self.gdb=gatedb.gatedb()
		self.interface='wlan0'
		logging.basicConfig(filename='/var/log/motion/gatekeeper.log',format='%(asctime)s %(levelname)s %(message)s',level=logging.DEBUG)

	DEFAULT_DEVIATION = 14 # % deviation of area

	# checks that area "a1" is within deviation "d" % from a2
	def within(self,a1,a2,d=DEFAULT_DEVIATION):
		df=(a1*d)/100 # deviation 
		res=( a1 < (a2+df) and a1 > (a2-df) ) # a within deviation range
		return res # a within deviation range
		
	# to find a given shape and area in the array loaded from databse
	def find_shape(self,shapes,vertices,area):
		logging.info("find vertices="+str(vertices)+" area="+str(area))
		lr=0
		for s in shapes:
			logging.debug("finding shape " + str(s))
			if ( s[2] == vertices ):
				if ( self.within(s[1],area) ):
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
		MIN_A = 17
		MAX_A = 50000
		return (A >= MIN_A and A <= MAX_A)

	def find_best_algorithm(self,imgnms,reg):
		cntspername={}
		delimiter=":"
		# reveal contours for all files in training and all available algorithms
		fnames=imgnms.split(",")
		for n in fnames:
			for a in (1,2,3,4,5):
				regn=self.patch_region(reg,a)
				cnts=self.get_contours(n,regn)
				cntspername[n+delimiter+str(a)]=cnts
		best_algo=-1
		max_features=-1
		best_fn="n/a"
		# find algorithms that reveal maximum features
		for ca in sorted(cntspername.keys()):
			cur_features = self.get_features(cntspername[ca])
			if ( len(cur_features) > max_features ):
				max_features=len(cur_features)
				best_algo = int(ca.split(delimiter)[1])
				best_fn=ca.split(delimiter)[0]
		avg_features={}
		# for the algorithm that reveals max features, build "average set" of features recognized on all pictures
		logging.debug("IV TRACE in region "+str(reg))
		for ca in sorted(cntspername.keys()):
			if ( int(ca.split(delimiter)[1]) == best_algo ):
				cur_features = self.get_features(cntspername[ca])
				for cf in cur_features:
					cfk=cf[1:]
					if cfk in avg_features.keys():
						avg_features[cfk] += 1
						logging.debug("IV TRACE NON first feature in average " + str(cf))
					else:
						avg_features[cfk] = 1
						logging.debug("IV TRACE first feature in average "+str(cf))
		many_files=3 # int(len(fnames) / 3)
		avg_features_set=[]
		num=0
		for k in avg_features.keys():
			if (avg_features[k] >= many_files):
				avg_features_set.append((num,k[0],k[1]))
				num+=1
		return (best_algo,best_fn,avg_features_set)

	def patch_region(self,reg,algo):
		return (reg[0],reg[1],reg[2],reg[3],reg[4],reg[5],algo)

	def snapshot_regions(self,imgnms,visual):
		for reg in self.gdb.get_reqions():
			(algo,fn,avg)=self.find_best_algorithm(imgnms,reg)
			self.gdb.update_algorithm(reg[0],algo)
			self.gdb.delete_features(reg[0])
			regn=self.patch_region(reg,algo)
			self.save_features(avg,regn)

	def check_features(self,imgn,regname,visual):
		reg=self.gdb.get_region(regname)
		shapes=self.gdb.load_features(reg[0])

		(res,cnt)= self.shapes_exist(imgn,reg,shapes,visual)
		logging.info("image="+imgn+" region="+regname+" res="+str(res)+" cnt="+str(cnt))
		return (res,cnt)

	def shapes_exist(self, image_name, reg, shapes_to_find, visual):
		cnts=self.get_contours(image_name, reg)
		if (visual):
			self.view_countours(cnts, image_name,reg)

		shapes =self.get_features(cnts)
		fcnt=0
		for s in shapes_to_find:
			if ( self.find_shape(shapes, s[2],s[1]) != None ):
				fcnt += 1
				logging.debug("shape found " + str(s))
			else:
				logging.debug("shape NOT found " + str(s))

		logging.info("fcnt="+str(fcnt)+" len(shapes_to_find)="+str(len(shapes_to_find)))
		return ((len(shapes_to_find) / 2 ) <= fcnt,fcnt)

	def reveal_contours(self,img,reg):
		algo=reg[6]
		img = self.read_region(img,reg)
		if ( algo == 2 ):
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.adaptiveThreshold(blurred, 255, cv2.CALIB_CB_ADAPTIVE_THRESH, cv2.THRESH_BINARY_INV, 11, 2)
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		if (algo == 3):
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.adaptiveThreshold(blurred, 128, cv2.CALIB_CB_ADAPTIVE_THRESH, cv2.THRESH_BINARY_INV, 11, 2)
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		elif ( algo == 4 ):
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.threshold(blurred, 55, 255, cv2.THRESH_BINARY_INV)[1]
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) #  NONE) # APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		elif (algo == 5):
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.threshold(blurred, 55, 255, cv2.THRESH_BINARY_INV)[1]
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # NONE) # APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		elif (algo == 1):
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (3, 3), 0)
			thresh = cv2.threshold(blurred, 55, 255, cv2.THRESH_BINARY_INV)[1]
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)  # NONE) # APPROX_SIMPLE)
			cnts = cnts[0] if imutils.is_cv2() else cnts[1]
			return cnts
		else:
			return None

	def check_garage_state(self,img,visual):
		(car,fcnt)=self.check_features(img, "car", visual)
		if fcnt > 0:
			if self.gdb.car() != car:
				self.gdb.save_car(car)
		(gate,fcnt)=self.check_features(img, "gate", visual)
		if fcnt > 0:
			if self.gdb.gate() != gate:
				self.gdb.save_gate(gate)
		return (car,gate)

	def get_contours(self, image, reg):
		if (not os.path.isfile(image)):
			logging.warn("image file not found " + image)
			return None
		sz = os.path.getsize(image)
		if (sz == 0L):
			logging.warn("image file empty, ignoring " + image)
			return None
		logging.info("detect_shapes image_name=" + image)
		cnts = self.reveal_contours(image,reg)
		return cnts

	def read_region(self,imgn,reg):
		img = cv2.imread(imgn)
		cropped = img[reg[3]:reg[5], reg[2]:reg[4]]
		return cropped

	def view_countours(self,cnts,img_nme, reg):
		if ( cnts == None ):
			return
		ratio=1
		img = self.read_region(img_nme, reg)
		for c in cnts:
			# compute the center of the contour, then detect the name of the
			# shape using only the contour
			M = cv2.moments(c)
			(vertices) = self.detect_shape(c)
			A = M["m00"]  # Area
			if ( not self.is_acceptable_area(A)):
				continue
			logging.info("in file" + img_nme + " recognized vertices=" + str(vertices)+ " area=" + str(A) )
			cX = int((M["m10"] / M["m00"]) * ratio)
			cY = int((M["m01"] / M["m00"]) * ratio)

			# multiply the contour (x, y)-coordinates by the resize ratio,
			# then draw the contours and the name of the shape on the image
#			c = c.astype("float")
#			c *= ratio
#			c = c.astype("int")
			cv2.drawContours(img, [c], -1, (0, 255, 0), 1)
#			cv2.putText(img, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

			# show the output image
			cv2.imshow("image", img)
			cv2.waitKey(0)

	def get_features(self,cnts):
		shapes = []
		if ( cnts == None ):
			return shapes
		snum=0
		for c in cnts:
			# compute the center of the contour, then detect the name of the
			# shape using only the contour
			M = cv2.moments(c)
			(vertices) = self.detect_shape(c)
			A = M["m00"]  # Area

			if (not self.is_acceptable_area(A)):
				continue
#				logging.debug("recognized shape=" + shape + " area=" + str(A) )
			shape=(snum,A,vertices)
			snum += 1
			shapes.append(shape)
		res= sorted(shapes, key=lambda x: str(x[2])+"{0:020.2f}".format(round(x[1],2)))
		return res

	def save_features(self, shapes, reg):
		for s in shapes:
			self.gdb.save_feature(s[1],s[2],reg[0])

	def gate_state_changed(self,new_state):
		logging.info("gate state changed, it is now open = "+str(new_state))
		self.gdb.save_gate(new_state)

	def detect_shape(self, c):
		peri = cv2.arcLength(c, True)
		approx = cv2.approxPolyDP(c, 0.04 * peri, True)
		return (len(approx))

	def ping6(self, interface, addr):
		# ping6 -c 1 -I wlan0 -w 1 ff02::1
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
		# ping6 -c 3 -I wlan0 ff02::1
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
    # fe80::6203:8ff:fe91:5c56 dev wlan0 lladdr 60:03:08:91:5c:56 REACHABLE
    # fe80::76d0:2bff:fecf:1257 dev wlan0 lladdr 74:d0:2b:cf:12:57 STALE

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
				neigh=self.broadcastPing6(self.interface,'1')
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
						self.ping6(self.interface, n['ip'])
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
							self.ping6(self.interface, n['ip'])
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
		gs=self.gdb.gate()
		logging.info("new neighbor "+ str(ln)+" gate state open = "+str(gs))
		if ( gs == False ):
			self.open_gate()
			
	def neighbor_away(self,ln):
		# check to see when status was last updated
		few_min_ago_ts=datetime.datetime.now() - datetime.timedelta(minutes=2)
		few_min_ago=few_min_ago_ts.strftime('%Y-%m-%d %H:%M:%S')
		logging.debug("neighbor went away "+ str(ln)+" min_ago "+few_min_ago)

		if ( few_min_ago > ln[2] ):
			if ( self.gdb.gate() ):
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
