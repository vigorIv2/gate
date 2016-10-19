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

	def checkgate(self,mygate_json,image_name) :
		if ( not os.path.isfile(image_name) ):
			logging.warn("image file not found "+image_name)
			return
		sz = os.path.getsize(image_name)
		if ( sz == 0L ):
			logging.warn("image file empty, ignoring "+image_name)
			return

		try:
			with open(mygate_json, 'r') as jsonfile:
				myg=jsonfile.read()
			jmyg=json.loads(myg)
			for l in jmyg["level"]:
				print l
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
		
			# loop over the contours
			for c in cnts:
				# compute the center of the contour, then detect the name of the
				# shape using only the contour
				#	print c
				M = cv2.moments(c)
				#	print M
				#	A = cv2.contourArea(c)
				shape = self.detect(c)
				A = M["m00"]
				print shape, " ", A
				if (A > 698 or A < 20):
					continue
				if (M["mu02"] < 100 ) :
					continue

				if (M["mu02"] > 26000 ) :
					continue

				if (M["m00"] == 0):
					M["m00"]=1
					continue

				cX = int((M["m10"] / M["m00"]) * ratio)
				cY = int((M["m01"] / M["m00"]) * ratio)

				if ( shape == "circle" and (A < 49 or A > 69)):
					continue
				if ( shape == "pentagon" and (A < 63 or A > 107)):
					continue
				if ( shape == "triangle" and (A < 41 or A > 84)):
					continue
				if ( shape == "rectangle" and (A < 107 or A > 152)):
					continue
				# multiply the contour (x, y)-coordinates by the resize ratio,
				# then draw the contours and the name of the shape on the image
				c = c.astype("float")
				c *= ratio
				c = c.astype("int")
				cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
				cv2.putText(image, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

				# show the output image
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
