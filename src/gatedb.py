#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.insert(1, '/home/iotuser/gate/web2py')

from gluon import DAL, Field
from gluon.validators import IS_NOT_EMPTY, IS_EMAIL, IS_NOT_IN_DB, IS_INT_IN_RANGE

db = None

def opendb():
	global db
	if ( db == None ):
#		print "open database DAL"
		db = DAL('sqlite://storage.sqlite', folder='/home/iotuser/gate/web2py/applications/gate/databases')
		execfile('/home/iotuser/gate/web2py/applications/gate/models/db_gate.py')

def closedb():
	global db
#	print "close database DAL"
	db.close()
	db = None

class gatedb:
	' module to maintan state in the database, sqlite3 for now should be sufficient '

	def __init__(self):
		opendb()
		return

	def close(self):
		closedb()
		return

	def open(self):
		opendb()
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
		self.open()
		res=db().select(db.trusted.ALL)
		return res

	def get_neighborhood_state(self):
		self.open()
		res=db().select(db.neighborhood.ALL)
		return res

	def gate(self):
		self.open()
		row=db().select(db.gate.ALL,orderby=~db.gate.ts, limitby=(0, 1) ).first()
		if row == None : return True
		return row.closed

	def get_region(self,regname):
		self.open()
		return db(db.region.name == regname).select()[0]

	def oui_vendor(self,_oui):
		self.open()
		return db(db.oui.oui == _oui).select()

	def car(self):
		self.open()
		row=db().select(db.car.ALL, orderby=~db.car.ts, limitby=(0, 1)).first()
		if row == None : return True
		return row.yes

	def save_gate(self, _closed=False): # 0 - False, 1 - True
		self.open()
		db.gate.insert(closed=(1 if _closed else 0))

	def save_neighbor_state(self, _state, _neighbor_id): 
		self.open()
		db(db.neighborhood.neighbor_id == _neighbor_id).delete()
		db.neighborhood.insert(state=_state, neighbor_id=_neighbor_id)

	def save_car(self, _yes=False): # 0 - False, 1 - True
		self.open()
		db.car.insert(yes=(1 if _yes else 0))

	def save_feature(self, _area, _vertices, _cx, _cy, _coveredByCar, _region_id):
		self.open()
		db.features.insert(area=_area, vertices=_vertices, cx=_cx, cy=_cy, coveredByCar=(1 if _coveredByCar else 0), region_id=_region_id)

	def load_features(self, regid):
		self.open()
		return db(db.features.region_id==regid).select()

	def delete_features(self, region_id):
		self.open()
		db(db.features.region_id == region_id).delete()

	def drop_neighbor_state(self, neib_id):
		self.open()
		db(db.neighborhood.neighbor_id == neib_id).delete()



