import cv2
import sys

# load the image and show it
image = cv2.imread(sys.argv[1])

startY=280; endY=640; startX=0; endX=310 # gate shapes

print (startY, endY, startX, endX)
# startY and endY coordinates, followed by the startX and endX 
cropped = image[startY:endY, startX:endX]
cv2.imshow("cropped", cropped)
cv2.waitKey(0)


#frame2 = i.crop(((left, upper, width, lower)))
#timage='tmp/dt110507dhct_frame2.jpg'
#frame2.save(timage)
#print "prior to imread"

#image = cv2.imread(timage)

#cv2.imshow("Image", image)
#cv2.waitKey(0)

