#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(1,'/home/iotuser/gate/web2py') 

from gluon import DAL, Field 
from gluon.validators import IS_NOT_EMPTY, IS_EMAIL, IS_NOT_IN_DB, IS_INT_IN_RANGE

db = DAL('sqlite://storage.sqlite',folder='/home/iotuser/gate/web2py/applications/gate/databases')
execfile('/home/iotuser/gate/web2py/applications/gate/models/db_gate.py')

print db.tables
print db().select(db.oui.ALL)
print db().select(db.security.ALL)
