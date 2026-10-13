PRAGMA foreign_keys=ON;

CREATE TABLE bookings (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	event_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (quantity > 0), 
	CHECK (status IN ('confirmed','cancelled')), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(event_id) REFERENCES events (id)
);

CREATE TABLE events (
	id INTEGER NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	description VARCHAR(1200) NOT NULL, 
	venue_id INTEGER NOT NULL, 
	organiser_id INTEGER NOT NULL, 
	starts_at DATETIME NOT NULL, 
	ticket_limit INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (ticket_limit > 0), 
	FOREIGN KEY(venue_id) REFERENCES venues (id), 
	FOREIGN KEY(organiser_id) REFERENCES users (id)
);

CREATE TABLE users (
	id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(180) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (role IN ('admin','organiser','staff','customer'))
);

CREATE TABLE venues (
	id INTEGER NOT NULL, 
	name VARCHAR(140) NOT NULL, 
	location VARCHAR(250) NOT NULL, 
	capacity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (capacity > 0), 
	UNIQUE (name)
);
