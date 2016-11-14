#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import time
import sys
import sqlite3

class gatedb:
	' module to maintan state in the database, sqlite3 for now should be sufficient '

	_db_sqlite3_name="../db/garage.db"

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
		for row in self.conn.execute('SELECT id, name, left, upper, right, lower FROM regions'):
			result.append(row)
		return result


	def get_files_before(self,current_file):
		ts=""
		for row1 in self.conn.execute('SELECT time_stamp FROM security where filename = ?',(current_file,)):
			ts=row1[0]
		result = []

		for row2 in self.conn.execute('SELECT filename FROM security where filename != ? and time_stamp <= ? and time_stamp >= datetime(?,"-5 minutes") order by time_stamp desc',(current_file,ts,ts,)):
			result.append(row2[0])

		return result

	def get_trusted_neighbors(self):
		result = []
		for row in self.conn.execute("SELECT id,ip,mac,name,datetime(ts, 'localtime') FROM trusted_neighbors ORDER BY id"):
			result.append(row)
		return result

	def gate_state(self):
		for row in self.conn.execute('select open from gate_state order by ts desc limit 1;'):
			return row[0] == 1
		return None

	def get_region(self,regname):
		for row in self.conn.execute('select id, left, upper, right, lower from regions where name = ? ',(regname,)):
			return row
		return None

	def oui_vendor(self,oui):
		for row in self.conn.execute('select vendor from oui_vendor where oui=?;',(oui,)):
			return row[0]
		return 'Unknown'

	def car_state(self):
		for row in self.conn.execute('select open from car_parked order by ts desc limit 1;'):
			return row[0] == 1
		return True # for now let us pretend it is always there

	def save_gate_state(self,gate_open = False): # 0 - False, 1 - True 
		with self.conn:
			self.conn.execute("insert into gate_state(open) values (?)", ((1 if gate_open else 0),))

	def save_neighbor_state(self,state,neib_id):  
		with self.conn:
			self.conn.execute("replace into neighborhood_state(state,neighbor_id) values (?,?)", (state,neib_id,))

	def save_shapes_regions(self,name,area,region_id):
		with self.conn:
			self.conn.execute("insert into shapes_regions(name,area,region_id) values (?,?,?)", (name,area,region_id,))

	def load_shapes(self,regid):
		result = []
		for row in self.conn.execute('select id, name, area from shapes_regions where region_id = ? ',(regid,)):
			result.append(row)
		return result

	def delete_shapes_regions(self,region_id):
		with self.conn:
			self.conn.execute("delete from shapes_regions where region_id = ?", (region_id,))

	def delete_file_record(self,fname):
		with self.conn:
			self.conn.execute("delete from security where filename=?", (fname,))

	def drop_neighbor_state(self,neib_id):
		with self.conn:
			self.conn.execute("delete from neighborhood_state where neighbor_id = ?;", (neib_id,))

	def get_neighborhood_state(self):
		result = []
		for row in self.conn.execute("SELECT neighbor_id,state,datetime(ts, 'localtime') FROM neighborhood_state ORDER BY neighbor_id, ts"):
			result.append(row)
		return result



