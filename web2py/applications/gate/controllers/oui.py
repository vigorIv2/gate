# -*- coding: utf-8 -*-
# try something like
response.menu = [['Register OUI', False, URL('register_oui')]]

def register_oui():
    # create an insert form from the table
    form = SQLFORM(db.oui).process()

    # if form correct perform the insert
    if form.accepted:
        response.flash = 'new OUI inserted'

    # and get a list of all oui
    records = SQLTABLE(db().select(db.oui.ALL),headers='fieldname:capitalize')

    return dict(form=form, records=records)
