# -*- coding: utf-8 -*-

def index():
    g=db().select(db.gate.ALL,orderby=~db.gate.id, limitby=(0, 1) ).first()
    c=db().select(db.car.ALL,orderby=~db.car.id, limitby=(0, 1) ).first()
    if g.closed :
       gate_status=DIV(T("Closed"),_style="color: red; font-weight: bold;")
    else:
       gate_status=DIV(T("Open"),_style="color: green; font-weight: bold;")
    if c.yes :
       car_status=DIV(T("Inside"),_style="color: purple; font-weight: bold;")
    else:
       car_status=DIV(T("Outside"),_style="color: blue; font-weight: bold;")
    return dict(gate=gate_status, car=car_status)
