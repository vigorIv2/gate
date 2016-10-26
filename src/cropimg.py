import Image
i = Image.open('./test/ccg2.jpg')
#(left, upper, width, lower)
frame2 = i.crop(((275, 0, 528, 250)))
frame2.save('dt110507dhct_frame2.jpg')
