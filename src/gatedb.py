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
		return result

	def get_events(self):
		result = []
		for row in self.conn.execute('SELECT * FROM security'):
			result.append(row)
		return result

	def get_reqions(self):
		result = []
		for row in self.conn.execute('SELECT id, name, left, upper, right, lower, algorithm FROM regions'):
			result.append(row)
		return result

	def get_files_before(self,current_file):
		ts=""
		for row1 in self.conn.execute('SELECT time_stamp FROM security where filename = ?', (current_file,)):
			ts=row1[0]
		result = []

		for row2 in self.conn.execute('SELECT filename FROM security where filename != ? and time_stamp <= ? and time_stamp >= datetime(?,"-5 minutes") order by time_stamp desc', (current_file,ts,ts,)):
			result.append(row2[0])

		return result

	def get_trusted_neighbors(self):
		result = []
		for row in self.conn.execute("SELECT id,ip,mac,name,datetime(ts, 'localtime') FROM trusted_neighbors ORDER BY id"):
			result.append(row)
		return result

	def gate(self):
		for row in self.conn.execute('select closed from gate order by ts desc limit 1;'):
			return row[0] == 1
		return None

	def get_region(self,regname):
		for row in self.conn.execute('select id, name, left, upper, right, lower, algorithm from regions where name=?;', (regname,)):
			return row
		return None

	def update_algorithm(self,id,algo):
		with self.conn:
			self.conn.execute("update regions set algorithm = ? where id = ?", (algo,id,))

	def oui_vendor(self,oui):
		for row in self.conn.execute('select vendor from oui_vendor where oui=?;',(oui,)):
			return row[0]
		return 'Unknown'

	def car(self):
		for row in self.conn.execute('select yes from car order by ts desc limit 1;'):
			return row[0] == 1
		return True # for now let us pretend it is always there

	def save_gate(self, closed=False): # 0 - False, 1 - True
		with self.conn:
			self.conn.execute("insert into gate(closed) values (?)", ((1 if closed else 0),))

	def save_car(self, yes=False): # 0 - False, 1 - True
		with self.conn:
			self.conn.execute("insert into car(yes) values (?)", ((1 if yes else 0),))

	def save_neighbor_state(self, state, neib_id):
		with self.conn:
			self.conn.execute("replace into neighborhood_state(state,neighbor_id) values (?,?)", (state,neib_id,))

	def save_feature(self, area, vertices, cx, cy, coveredByCar, region_id):
		with self.conn:
			self.conn.execute("insert into feature(area,vertices,cx,cy,coveredByCar,region_id) values (?,?,?,?,?,?)", (area,vertices,cx,cy,(1 if coveredByCar else 0),region_id,))

	def load_features(self, regid):
		result = []
		for row in self.conn.execute('select id, area, vertices, cx, cy, coveredByCar from feature where region_id = ? ', (regid,)):
			result.append(row)
		return result

	def delete_features(self, region_id):
		with self.conn:
			self.conn.execute("delete from feature where region_id = ?", (region_id,))

	def delete_file_record(self, fname):
		with self.conn:
			self.conn.execute("delete from security where filename=?", (fname,))

	def drop_neighbor_state(self, neib_id):
		with self.conn:
			self.conn.execute("delete from neighborhood_state where neighbor_id = ?;", (neib_id,))

	def get_neighborhood_state(self):
		result = []
		for row in self.conn.execute("SELECT neighbor_id,state,datetime(ts, 'localtime') FROM neighborhood_state ORDER BY neighbor_id, ts"):
			result.append(row)
		return result



