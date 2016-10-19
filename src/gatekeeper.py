import os
import logging
import json
import time
import sys
import subprocess
import imutils
import cv2

class GateKeeper:
	' Common base class for GateKeeper software '

	def __init__(self, ):
		logging.basicConfig(filename='/var/log/motion/gatekeeper.log',format='%(asctime)s %(levelname)s %(message)s',level=logging.DEBUG)

	DEFAULT_DEVIATION=7 # 5% deviation of area

	# checks that area "a1" is within deviation "d" % fomr a2
	def within(self,a1,a2,d=DEFAULT_DEVIATION):
		df=(a1*d)/100 # deviation 
		res=( a1 < (a2+df) and a1 > (a2-df) ) # a within deviation range
		return res # a within deviation range
		
  # to find a given shape and area in 
	def find_shape(self,jmygate,shape,area):
		lr=0
		for l in jmygate["levels"]:
#			print l
			for s in l["shapes"]:
				rshape = unicode(shape, "utf-8")
				if ( rshape == u'square' ):
					rshape = u'rectangle' # treat square as rectangles
				if ( rshape in s[u'shape'] ):
					a1=s[u'area']
					if ( self.within(a1,area) ):
						return lr
			lr+=1
		return None
		
	def checkgate(self,mygate_json,image_name,visual_trace = True) :
		if ( not os.path.isfile(image_name) ):
			logging.warn("image file not found "+image_name)
			return
		sz = os.path.getsize(image_name)
		if ( sz == 0L ):
			logging.warn("image file empty, ignoring "+image_name)
			return

		logging.info("processing image_name="+image_name+" json="+mygate_json)
		try:
			with open(mygate_json, 'r') as jsonfile:
				myg=jsonfile.read()
			jmyg=json.loads(myg)
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
			# loop over the contours
			for c in cnts:
				# compute the center of the contour, then detect the name of the
				# shape using only the contour
				M = cv2.moments(c)
				shape = self.detect(c)
				A = M["m00"] # Area
				L = self.find_shape(jmyg,shape,A)
				if ( A > 20) :
					print "trying ",shape, " ", A, " ", L
				if ( L == None ):
					continue
				if ( L < ML ):
					continue
				ML = L
				print "recognized", shape, " ", A, " ", L
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
					cv2.imshow("Image", image)
					cv2.waitKey(0)

		except Exception, err:
			logging.exception('Error from throws():')


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
