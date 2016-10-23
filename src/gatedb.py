#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import time
import sys
import sqlite3

class gatedb:
	' module to maintan state in the database, sqlite3 for now should be sufficient '

	_db_sqlite3_name="/opt/data/sqlite3/garage.db"

	def __init__(self):
		conn = sqlite3.connect(self._db_sqlite3_name)
		return

