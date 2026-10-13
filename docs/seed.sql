-- Illustrative seeded data, adapted from working local demonstration DB.
-- Import into an EMPTY database after schema.sql.
-- Password hashes are fictional demo credentials.
PRAGMA foreign_keys=ON;
INSERT INTO users (id, name, email, password_hash, role) VALUES (1, 'Project Admin', 'admin@demo.example.com', 'pbkdf2_sha256$260000$858288aab92eb768f7703813231d1a79$649a67a860355c1f25b2cf8249d52cbc148eeb46cffd718108b9d4fbc243a625', 'admin');
INSERT INTO users (id, name, email, password_hash, role) VALUES (2, 'Event Organiser', 'organiser@demo.example.com', 'pbkdf2_sha256$260000$c06eef36c72b6a65ba22cd5888e8fd89$a59339e9c927432a125677cac2b9bb062be5131779ac5eddee71541de8f1121f', 'organiser');
INSERT INTO users (id, name, email, password_hash, role) VALUES (3, 'Venue Staff', 'staff@demo.example.com', 'pbkdf2_sha256$260000$2c20b348b216ca254d2277898542d7c7$1f6e8638ae189e023804d5ffbc9ee7e2db0e2a065da84727ea24dbf21c761796', 'staff');
INSERT INTO users (id, name, email, password_hash, role) VALUES (4, 'Customer One', 'customer1@demo.example.com', 'pbkdf2_sha256$260000$5dbd9f518d5acdfe63d2a159901e61a7$8d0a46cb98c3fa5b059f0d500fca78e09c243cf3727433e981b2f69665b17424', 'customer');
INSERT INTO users (id, name, email, password_hash, role) VALUES (5, 'Customer Two', 'customer2@demo.example.com', 'pbkdf2_sha256$260000$425a10bb8cf4ffdc5319dde233fb3f4f$0869ac4d0257d774c621e75575adbd6f95aef4b997979c6d4cc43165fae0a226', 'customer');
INSERT INTO venues (id, name, location, capacity) VALUES (1, 'Grand Hall', 'Kuala Lumpur', 500);
INSERT INTO venues (id, name, location, capacity) VALUES (2, 'Sky Auditorium', 'Shah Alam', 200);
INSERT INTO venues (id, name, location, capacity) VALUES (3, 'Open Garden', 'Putrajaya', 300);
INSERT INTO venues (id, name, location, capacity) VALUES (4, 'Creative Studio', 'Petaling Jaya', 80);
INSERT INTO venues (id, name, location, capacity) VALUES (5, 'City Arena', 'Cyberjaya', 1000);
INSERT INTO events (id, name, description, venue_id, organiser_id, starts_at, ticket_limit) VALUES (1, 'Tech Futures Expo', 'Fictional demonstration event', 1, 2, '2026-10-28 21:55:02.494530', 50);
INSERT INTO events (id, name, description, venue_id, organiser_id, starts_at, ticket_limit) VALUES (2, 'Community Music Night', 'Fictional demonstration event', 2, 2, '2026-10-29 21:55:02.495512', 75);
INSERT INTO events (id, name, description, venue_id, organiser_id, starts_at, ticket_limit) VALUES (3, 'Startup Pitch Day', 'Fictional demonstration event', 3, 2, '2026-10-30 21:55:02.495920', 100);
INSERT INTO events (id, name, description, venue_id, organiser_id, starts_at, ticket_limit) VALUES (4, 'Digital Art Workshop', 'Fictional demonstration event', 4, 2, '2026-10-31 21:55:02.496315', 80);
INSERT INTO events (id, name, description, venue_id, organiser_id, starts_at, ticket_limit) VALUES (5, 'University Career Fair', 'Fictional demonstration event', 5, 2, '2026-11-01 21:55:02.496679', 150);
INSERT INTO bookings (id, user_id, event_id, quantity, status, created_at) VALUES (1, 4, 1, 2, 'confirmed', '2026-10-08 21:55:02.499705');
INSERT INTO bookings (id, user_id, event_id, quantity, status, created_at) VALUES (2, 4, 2, 2, 'confirmed', '2026-10-08 21:55:02.500332');
INSERT INTO bookings (id, user_id, event_id, quantity, status, created_at) VALUES (3, 4, 3, 2, 'confirmed', '2026-10-08 21:55:02.500649');
INSERT INTO bookings (id, user_id, event_id, quantity, status, created_at) VALUES (4, 4, 4, 2, 'confirmed', '2026-10-08 21:55:02.500925');
INSERT INTO bookings (id, user_id, event_id, quantity, status, created_at) VALUES (5, 4, 5, 2, 'confirmed', '2026-10-08 21:55:02.501148');
