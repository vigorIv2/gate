#!/usr/bin/python 
from flask import Flask

import sys
import time
import logging
import RPi.GPIO as GPIO ## Import GPIO library

def push_button(button):
  print >> sys.stderr, "push_button begin"
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BOARD)
  GPIO.setup(15, GPIO.OUT)
  GPIO.output(15,False)
  time.sleep(4)
  GPIO.output(15,True)
  print >> sys.stderr, "push_button end"

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')

def catch_all(path):
  if (path.startswith("button2")):
  	push_button("2")
  return 'You want path: %s' % path

if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=6543)
  app.run(host='::', port=6543)
