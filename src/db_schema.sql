DROP TABLE if exists security;

CREATE TABLE if not exists security(
	camera int,
	filename varchar(128) not null,
	frame int,
	file_type int,
	time_stamp timestamp(14),
	text_event varchar(40)
);

DROP TABLE if exists trusted_neighbors;

CREATE TABLE if not exists trusted_neighbors(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	ip varchar(128),
	mac varchar(40),
	name varchar(40),
	ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

delete from trusted_neighbors;
-- insert into trusted_neighbors(ip,mac,name) values('fe80::f66d:4ff:fe24:e024', 'f4:6d:04:24:e0:24', 'Asustek Tablet');
insert into trusted_neighbors(ip,mac,name) values('fe80::14cf:84b3:d7bb:4839', '30:63:6b:b0:5e:4e', 'Apple iPhone Blizz');
-- insert into trusted_neighbors(ip,mac,name) values('fe80::b607:f9ff:feee:20d7', 'b4:07:f9:ee:20:d7', 'Samsung G1');
-- insert into trusted_neighbors(ip,mac,name) values('fe80::b6ce:f6ff:fedf:947', 'b4:ce:f6:df:09:47', 'Google Nexus 9');
-- insert into trusted_neighbors(ip,mac,name) values('fe80::8ae:b4e3:4250:f62c', '90:8d:6c:cd:b2:d4', 'Apple iPhone, Owl');
select * from trusted_neighbors;

DROP TABLE if exists regions;

CREATE TABLE if not exists regions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name varchar(40),
  left int, 
  upper int,
  right int,
  lower int,
  algorithm int,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

delete from regions;
insert into regions(name,left,upper,right,lower,algorithm) values('all', 0, 0, 480, 640, 1);

insert into regions(name,left,upper,right,lower,algorithm) values('car', 0, 280, 310, 640, 1);
insert into regions(name,left,upper,right,lower,algorithm) values('gate', 305, 70, 417, 350, 1);
select * from regions;


DROP TABLE if exists neighborhood_state;

CREATE TABLE if not exists neighborhood_state(
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  state varchar(40),
  neighbor_id INTEGER,
  FOREIGN KEY(neighbor_id) REFERENCES trusted_neighbors(id)
);
CREATE UNIQUE INDEX neighbor_state_idx on neighborhood_state (state,neighbor_id);

DROP TABLE if exists gate_button;

CREATE TABLE if not exists gate_button(
  no tinyint,
  kind varchar(20),
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

DROP TABLE if exists oui_vendor;

CREATE TABLE if not exists oui_vendor(
	oui char(8),
	vendor varchar(50)
);
CREATE UNIQUE INDEX oui_idx on oui_vendor (oui);
insert into oui_vendor(oui,vendor) values('f4:6d:04','Asustek');
insert into oui_vendor(oui,vendor) values('30:63:6b','Apple');
insert into oui_vendor(oui,vendor) values('a4:c4:94','Intel');
insert into oui_vendor(oui,vendor) values('b4:07:f9','Samsung');
insert into oui_vendor(oui,vendor) values('90:8d:6c','iPhone');
insert into oui_vendor(oui,vendor) values('b4:ce:f6','Nexus 9');

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

DROP TABLE if exists known_shapes;

CREATE TABLE if not exists known_shapes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name varchar(40),
  area float
);

truncate known_shapes;
insert into known_shapes(name,area) values('pentagon', 105);


insert into known_shapes(name,area) values('rectangle', 109.67);
insert into known_shapes(name,area) values('triangle', 83.17);

insert into known_shapes(name,area) values('pentagon', 65);
insert into known_shapes(name,area) values('circle', 50.5);
insert into known_shapes(name,area) values('circle', 64);

insert into known_shapes(name,area) values('triangle', 64);
insert into known_shapes(name,area) values('rectangle', 147.67);
select * from known_shapes;


DROP TABLE if exists shapes_regions;

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
