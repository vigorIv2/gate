DROP TABLE if exists security;

CREATE TABLE if not exists security(
	camera int,
	filename varchar(128) not null,
	frame int,
	file_type int,
	time_stamp timestamp(14),
	text_event varchar(40)
);

DROP TABLE if exists trusted;

CREATE TABLE if not exists trusted(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	ip varchar(128),
	mac varchar(40),
	name varchar(40),
	ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

delete from trusted;
-- insert into trusted(ip,mac,name) values('fe80::f66d:4ff:fe24:e024', 'f4:6d:04:24:e0:24', 'Asustek Tablet');
-- insert into trusted(ip,mac,name) values('fe80::14cf:84b3:d7bb:4839', '30:63:6b:b0:5e:4e', 'Apple iPhone Blizz');
insert into trusted(ip,mac,name) values('fe80::b607:f9ff:feee:20d7', 'b4:07:f9:ee:20:d7', 'Samsung G1');
-- insert into trusted(ip,mac,name) values('fe80::b6ce:f6ff:fedf:947', 'b4:ce:f6:df:09:47', 'Google Nexus 9');
-- insert into trusted(ip,mac,name) values('fe80::8ae:b4e3:4250:f62c', '90:8d:6c:cd:b2:d4', 'Apple iPhone, Owl');
select * from trusted;

DROP TABLE if exists region;

CREATE TABLE if not exists region(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name varchar(40),
  left int, 
  upper int,
  right int,
  lower int,
  algorithm int,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

delete from region;
insert into region(name,left,upper,right,lower,algorithm) values('all', 0, 0, 480, 640, 1);

insert into region(name,left,upper,right,lower,algorithm) values('car', 0, 280, 310, 640, 1);
insert into region(name,left,upper,right,lower,algorithm) values('gate', 305, 70, 417, 350, 1);
select * from region;


DROP TABLE if exists neighborhood;

CREATE TABLE if not exists neighborhood(
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  state varchar(40),
  neighbor_id INTEGER,
  FOREIGN KEY(neighbor_id) REFERENCES trusted(id)
);
CREATE UNIQUE INDEX neighbor_idx on neighborhood(state,neighbor_id);

DROP TABLE if exists gate_button;

CREATE TABLE if not exists gate_button(
  no tinyint,
  kind varchar(20),
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

DROP TABLE if exists oui;

CREATE TABLE if not exists oui(
	oui char(8),
	vendor varchar(50)
);
CREATE UNIQUE INDEX oui_idx on oui(oui);
insert into oui(oui,vendor) values('f4:6d:04','Asustek');
insert into oui(oui,vendor) values('30:63:6b','Apple');
insert into oui(oui,vendor) values('a4:c4:94','Intel');
insert into oui(oui,vendor) values('b4:07:f9','Samsung');
insert into oui(oui,vendor) values('90:8d:6c','iPhone');
insert into oui(oui,vendor) values('b4:ce:f6','Nexus 9');
select * from oui;

DROP TABLE if exists gate;

CREATE TABLE if not exists gate(
  closed boolean,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

DROP TABLE if exists car;

CREATE TABLE if not exists car(
  yes boolean,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

DROP TABLE if exists feature;

CREATE TABLE if not exists feature(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vertices int,
  area float,
  cx int,
  cy int,
  coveredByCar boolean,
  region_id INTEGER,
  FOREIGN KEY(region_id) REFERENCES regions(id)
);
-- CREATE UNIQUE INDEX feature_idx on feature (shape,vertices,area,region_id);
