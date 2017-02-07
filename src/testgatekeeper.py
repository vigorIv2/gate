#!/usr/bin/env python
# from __future__ import absolute_import

import unittest2 as unittest

import gatekeeper
import os

class TestGateKeeper(unittest.TestCase):

	def test_ngcco01(self):
		gk = gatekeeper.GateKeeper()
		cwd = os.getcwd()
		ffn=cwd+"/test/ngcco01.jpg"
		print("Checking "+ffn)
		(car, gate) = gk.check_garage_state(ffn, False)
		self.assertTrue(gate)
		self.assertFalse(car)

	def test_ngcco02(self):
		gk = gatekeeper.GateKeeper()
		cwd = os.getcwd()
		ffn = cwd + "/test/ngcco02.jpg"
		print("Checking " + ffn)
		(car, gate) = gk.check_garage_state(ffn, False)
		self.assertTrue(gate)
		self.assertFalse(car)

	def test_ngcco03(self):
		gk = gatekeeper.GateKeeper()
		cwd = os.getcwd()
		ffn = cwd + "/test/ngcco03.jpg"
		print("Checking " + ffn)
		(car, gate) = gk.check_garage_state(ffn, False)
		self.assertTrue(gate)
		self.assertFalse(car)

	def test_ngcco04(self):
		gk = gatekeeper.GateKeeper()
		cwd = os.getcwd()
		ffn = cwd + "/test/ngcco04.jpg"
		print("Checking " + ffn)
		(car, gate) = gk.check_garage_state(ffn, False)
		self.assertTrue(gate)
		self.assertFalse(car)

	def test_ngcco05(self):
		gk = gatekeeper.GateKeeper()
		cwd = os.getcwd()
		ffn = cwd + "/test/ngcco05.jpg"
		print("Checking " + ffn)
		(car, gate) = gk.check_garage_state(ffn, False)
		self.assertTrue(gate)
		self.assertFalse(car)

	def test_ngcco06(self):
		gk = gatekeeper.GateKeeper()
		cwd = os.getcwd()
		ffn = cwd + "/test/ngcco06.jpg"
		print("Checking " + ffn)
		(car, gate) = gk.check_garage_state(ffn, False)
		self.assertTrue(gate)
		self.assertFalse(car)

#    def test_split(self):
#        s = 'hello world'
#        self.assertEqual(s.split(), ['hello', 'world'])
#        # check that s.split fails when the separator is not a string
#        with self.assertRaises(TypeError):
#            s.split(2)

if __name__ == '__main__':
    unittest.main()
