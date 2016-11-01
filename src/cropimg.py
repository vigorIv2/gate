import cv2
import sys
import Image

image_name=sys.argv[1]
i = Image.open(image_name)
w= i.size[0]
h= i.size[1]

#left=0; upper=(h/8)*3+40; width=(w/8)*6-40; lower=h # ford silver
left=(w/8)*6-55; upper=0; width=w-63; lower=h # gate shapes

print (left, upper, width, lower)
frame2 = i.crop(((left, upper, width, lower)))
timage='tmp/dt110507dhct_frame2.jpg'
frame2.save(timage)
print "prior to imread"

image = cv2.imread(timage)

cv2.imshow("Image", image)
cv2.waitKey(0)

