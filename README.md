# Event Ticketing and Venue Booking System (SWC3633)

Educational reference implementation with a **shared FastAPI/SQLite REST backend** and **three different student-facing HTML frontends**.

## Setup

```bash
cd event_ticketing_code
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m backend.seed
uvicorn backend.main:app --reload
```

Visit http://127.0.0.1:8000/frontend/customer.html (student 1), `/frontend/organiser.html` (student 2), `/frontend/staff.html` (student 3), and `/docs` for all endpoints.

Demo logins: `admin@demo.example.com`, `organiser@demo.example.com`, `staff@demo.example.com`, `customer1@demo.example.com` / password `DemoPass123!`. Change demo passwords and `JWT_SECRET` before any public deployment. These accounts are fictional demonstration data.

## Requirements implemented

- Relational tables `users`, `venues`, `events`, `bookings`, with foreign keys, checks, and seed data (five each)
- CRUD for venues, events and bookings; user registration/list/details/delete with permission safeguards
- JWT access tokens, role checks, input validation, unified FastAPI errors
- Search and pagination for events, availability, status-aware cancellation
- External HTTP integration at `GET /bookings/{id}/qr`, which contacts GoQR's public `api.qrserver.com` QR code generator and reports its response metadata; live access to the external service is required
- Auto-generated OpenAPI at `/openapi.json`, Swagger `/docs`, and three student frontends

## Important project limitations and security considerations

This is a local demo, not a hardened production system. In SQLite, simultaneous booking writes may race; for production, use a transactional locking/reservation design with a suitable database. Add production logging, rate limiting, email verification, CSRF/threat-model review, HTTPS, stronger policy handling and automated integration tests. The external QR service generates a QR image from a demonstrative payload; it is not a secure signed admission token.

## Suggested manual test flow

1. Seed and run the backend.
2. Open Swagger docs; authenticate with an appropriate account.
3. GET `/events` (200); POST `/events` as a customer (403); POST with manager (201).
4. POST `/bookings` as a customer (201); GET `/bookings` (200); DELETE `/bookings/{id}` (200).
5. GET `/bookings/999999` (404); log in with wrong password (401); exceed event capacity (409).
6. GET `/bookings/{id}/qr` with a confirmed booking (200 when external provider works), save provider evidence.
7. Capture actual Postman evidence for both success and error cases; capture each frontend's actual workflow.

## Postman

Import `docs/postman_collection.json`, change baseUrl if needed, login, and manually set the bearer token in the collection Authorization tab or run login and paste the token.
