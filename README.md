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