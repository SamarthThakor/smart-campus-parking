
CREATE TABLE building (
	building_id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	latitude NUMERIC(9, 6) NOT NULL, 
	longitude NUMERIC(9, 6) NOT NULL, 
	PRIMARY KEY (building_id)
)

;


CREATE TABLE parking_lot (
	lot_id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	capacity INTEGER NOT NULL, 
	available_spaces INTEGER NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	latitude NUMERIC(9, 6) NOT NULL, 
	longitude NUMERIC(9, 6) NOT NULL, 
	updated_at VARCHAR(32) NOT NULL, 
	PRIMARY KEY (lot_id), 
	CONSTRAINT ck_lot_capacity CHECK (capacity > 0), 
	CONSTRAINT ck_lot_spaces CHECK (available_spaces >= 0 AND available_spaces <= capacity), 
	CONSTRAINT ck_lot_status CHECK (status IN ('open','closed'))
)

;


CREATE TABLE permit_type (
	permit_id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (permit_id), 
	UNIQUE (name)
)

;


CREATE TABLE lot_permit (
	lot_id INTEGER NOT NULL, 
	permit_id INTEGER NOT NULL, 
	PRIMARY KEY (lot_id, permit_id), 
	FOREIGN KEY(lot_id) REFERENCES parking_lot (lot_id), 
	FOREIGN KEY(permit_id) REFERENCES permit_type (permit_id)
)

;


CREATE TABLE user (
	user_id INTEGER NOT NULL AUTO_INCREMENT, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	`role` VARCHAR(10) NOT NULL, 
	permit_id INTEGER, 
	PRIMARY KEY (user_id), 
	CONSTRAINT ck_user_role CHECK (role IN ('student','admin')), 
	UNIQUE (email), 
	FOREIGN KEY(permit_id) REFERENCES permit_type (permit_id)
)

;


CREATE TABLE walk_estimate (
	lot_id INTEGER NOT NULL, 
	building_id INTEGER NOT NULL, 
	walking_minutes INTEGER NOT NULL, 
	PRIMARY KEY (lot_id, building_id), 
	CONSTRAINT ck_walk_minutes CHECK (walking_minutes > 0), 
	FOREIGN KEY(lot_id) REFERENCES parking_lot (lot_id), 
	FOREIGN KEY(building_id) REFERENCES building (building_id)
)

;


CREATE TABLE class_session (
	class_id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	building_id INTEGER NOT NULL, 
	title VARCHAR(100) NOT NULL, 
	weekday INTEGER NOT NULL, 
	start_time TIME NOT NULL, 
	end_time TIME NOT NULL, 
	PRIMARY KEY (class_id), 
	CONSTRAINT ck_class_weekday CHECK (weekday >= 0 AND weekday <= 6), 
	CONSTRAINT ck_class_time CHECK (end_time > start_time), 
	FOREIGN KEY(user_id) REFERENCES user (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(building_id) REFERENCES building (building_id)
)

;
CREATE INDEX ix_class_user_day ON class_session (user_id, weekday);