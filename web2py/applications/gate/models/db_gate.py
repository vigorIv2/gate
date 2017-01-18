# in file: models/db_custom.py
# db = DAL ('sqlite://garage.db')

import datetime

db.define_table(
   'oui',
   Field("oui", "string", length=8, notnull=True),
   Field('vendor', 'string', length=50, notnull = True)
)

db.define_table(
   'security',
   Field("camera", "integer"),
   Field('filename', 'string', length=128, notnull = True),
   Field('frame', 'integer'),
   Field('file_type', 'integer'),
   Field('time_stamp', 'datetime'),
   Field('text_event', 'string', length=40)
)

db.define_table(
   'region',
   Field('name', 'string', length=40, notnull = True),
   Field('left', 'integer'),
   Field('upper', 'integer'),
   Field('right', 'integer'),
   Field('lower', 'integer'),
   Field('algorithm', 'integer'),
)

db.define_table(
   'trusted',
   Field('ip', 'string', length=128, notnull = True),
   Field('mac', 'string', length=40),
   Field('name', 'string', length=40),
   Field('ts', 'datetime', default=datetime.datetime.now(), update=datetime.datetime.now(), writable=False)
)

db.define_table(
   'neighborhood',
   Field('state', 'string', length=40, notnull = True),
   Field('neighbor_id', db.trusted),
   Field('ts', 'datetime', default=datetime.datetime.now(), update=datetime.datetime.now(), writable=False)
)

db.define_table(
   'gate',
   Field('closed', 'boolean',  notnull = True),
   Field('ts', 'datetime', default=datetime.datetime.now(), update=datetime.datetime.now(), writable=False)
)

db.define_table(
   'car',
   Field('yes', 'boolean',  notnull = True),
   Field('ts', 'datetime', default=datetime.datetime.now(), update=datetime.datetime.now(), writable=False)
)

db.define_table(
   'features',
   Field('vertices', 'integer', notnull = True),
   Field('area', 'float'),
   Field('cx', 'integer'),
   Field('cy', 'integer'),
   Field('coveredByCar', 'boolean'),
   Field('region_id', db.region),
   Field('ts', 'datetime', default=datetime.datetime.now(), update=datetime.datetime.now(), writable=False)
)

db.define_table(
    'person',
    Field('name'),
    Field('email'),
    format = '%(name)s')

# ONE (person) TO MANY (products)

db.define_table(
    'product',
    Field('seller_id',db.person),
    Field('name'),
    Field('description', 'text'),
    Field('picture', 'upload', default=''),
    format = '%(name)s')

# MANY (persons) TO MANY (purchases)

db.define_table(
    'purchase',
    Field('buyer_id', db.person),
    Field('product_id', db.product),
    Field('quantity', 'integer'),
    format = '%(quantity)s %(product_id)s -> %(buyer_id)s')

purchased = (db.person.id==db.purchase.buyer_id)&(db.product.id==db.purchase.product_id)

db.person.name.requires = IS_NOT_EMPTY()
db.person.email.requires = [IS_EMAIL(), IS_NOT_IN_DB(db, 'person.email')]
db.product.name.requires = IS_NOT_EMPTY()
db.purchase.quantity.requires = IS_INT_IN_RANGE(0, 10)
