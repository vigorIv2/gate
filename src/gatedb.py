#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import time
import sys
import sqlite3

class gatedb:
	' module to maintan state in the database, sqlite3 for now should be sufficient '

	_db_sqlite3_name="/opt/data/sqlite3/garage.db"

	conn = None 
	def __init__(self):
		self.conn = sqlite3.connect(self._db_sqlite3_name)
		return

	def get_shapes(self):
		result = []
		for row in self.conn.execute('SELECT * FROM known_shapes ORDER BY id'):
			result.append(row)
#		print result
		return result
