#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import time
import sys
import sqlite3

class gatedb:
	' module to maintan state in the database, sqlite3 for now should be sufficient '

	_db_sqlite3_name="db/garage.db"

	conn = None 
	def __init__(self):
		self.conn = sqlite3.connect(self._db_sqlite3_name)
		return

	def get_shapes(self):
		result = []
		for row in self.conn.execute('SELECT * FROM known_shapes ORDER BY id'):
			result.append(row)
		return result

	def save_gate_state(self,gate_open = False): # 0 - False, 1 - True 
		with self.conn:
			self.conn.execute("insert into gate_state(open) values (?)", ((1 if gate_open else 0),))
