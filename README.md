# EVE Healthcare Diagnostic Booking API

A backend service for diagnostic test bookings and simulated payments, built as part of the EVE Healthcare SDE Intern Backend Engineering Assignment.

---

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
- Pydantic

---

## Project Structure

```text
eve-healthcare-backend/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   └── __init__.py
│   │
│   ├── database/
│   │   ├── session.py
│   │   └── __init__.py
│   │
│   ├── main.py
│   └── __init__.py
│
├── alembic/
├── tests/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md


## Database Schema

The application uses PostgreSQL with SQLAlchemy as the ORM and Alembic for database migrations.

### Tables

#### users

Stores registered users.

- `id`
- `name`
- `email`
- `password_hash`
- `created_at`

#### diagnostic_centres

Stores diagnostic centre information.

- `id`
- `name`
- `location`
- `created_at`

#### diagnostic_tests

Stores diagnostic tests.

- `id`
- `name`
- `description`

#### centre_tests

Associates diagnostic centres with the tests they offer.

- `id`
- `centre_id`
- `test_id`
- `price`

A unique constraint on `(centre_id, test_id)` prevents duplicate centre-test entries.

#### bookings

Stores diagnostic test appointments.

- `id`
- `user_id`
- `centre_test_id`
- `appointment_at`
- `amount`
- `status`
- `created_at`
- `updated_at`

The booking stores a snapshot of the test price at the time of booking so future catalogue price changes do not affect existing bookings.

Booking statuses:

- `PENDING`
- `CONFIRMED`
- `FAILED`
- `CANCELLED`

#### payments

Stores simulated payment information.

- `id`
- `booking_id`
- `payment_reference`
- `amount`
- `status`
- `created_at`
- `updated_at`

Each booking has at most one payment record in the current implementation.

Payment statuses:

- `SUCCESS`
- `FAILED`

#### webhook_events

Stores received payment webhook events.

- `id`
- `event_id`
- `event_type`
- `processed`
- `payload`
- `received_at`
- `processed_at`

`event_id` is unique to support idempotent webhook processing.

### Relationships

```text
User 1 ─────── N Booking

DiagnosticCentre 1 ─────── N CentreTest
DiagnosticTest   1 ─────── N CentreTest

CentreTest 1 ─────── N Booking

Booking 1 ─────── 1 Payment