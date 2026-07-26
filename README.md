# TashiHome Backend

TashiHome Backend is a FastAPI-based backend service for the TashiHome homestay platform. It provides authentication, user profile management, location management, settings, token handling, login logging, and Redis-backed event processing.

## Features

- JWT-based authentication and refresh-token flow
- User profile and role management
- Country, city, and location management
- Application settings and configuration APIs
- Login logging and IP-based metadata support
- Async SQLAlchemy + PostgreSQL integration
- Alembic migrations and Redis event subscriber support

## Tech stack

- Python 3.14+
- FastAPI
- SQLAlchemy + asyncpg
- PostgreSQL
- Redis
- Alembic
- Pydantic settings

## Getting started

1. Create a Python environment and install dependencies.
   - With uv:
     - `uv sync`
   - Or with pip:
     - `pip install -r requirements.txt` (if present) or `pip install -e .`

2. Configure environment variables.
   - Copy `.env.example` to `.env` and fill in the required values.
   - Make sure `DATABASE_URL`, `JWT_SECRET`, and other settings are defined.

3. Run database migrations.
   - `alembic upgrade head`

4. Start the application.
   - `uvicorn main:app --reload`
   - Or run `python main.py`

## Project docs

- [structure.md](structure.md) — project layout and architecture
- [phases.md](phases.md) — planned implementation phases and roadmap
- [database.md](database.md) — database schema and migration notes

## API entry point

The API is mounted under `/api/v1` in the main FastAPI app.
