#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.insert(1, '/home/iotuser/gate/web2py')

from gluon import DAL, Field
from gluon.validators import IS_NOT_EMPTY, IS_EMAIL, IS_NOT_IN_DB, IS_INT_IN_RANGE

db = DAL('sqlite://storage.sqlite', folder='/home/iotuser/gate/web2py/applications/gate/databases')
execfile('/home/iotuser/gate/web2py/applications/gate/models/db_gate.py')

class gatedb:
	' module to maintan state in the database, sqlite3 for now should be sufficient '

	def __init__(self):
		return

	def close(self):
		return

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
#		db(db.my_table.id > 0).select()
		return db(db.region.name == regname).select()


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

	def drop_neighbor_state(self, neib_id):
		with self.conn:
			self.conn.execute("delete from neighborhood_state where neighbor_id = ?;", (neib_id,))



