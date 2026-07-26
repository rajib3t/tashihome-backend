# Database design

The backend uses PostgreSQL with SQLAlchemy async models and Alembic migrations.

## Core tables

### users

Stores user identity, authentication data, and account state.

Key fields:
- id: primary key
- public_id: UUID for external references
- email: unique login identifier
- phone: optional unique phone number
- full_name: display name
- password: hashed password
- role: admin, vendor, or user
- status: active, inactive, or suspended
- timestamps: created_at, updated_at

### countries

Stores country records used for location-based features.

Key fields:
- id, public_id
- name: unique country name
- code: unique country code
- status: active or inactive
- timestamps

### cities and locations

The project also includes models for cities and locations, which are related to countries and support location-based APIs.

### tokens

Stores authentication tokens and refresh-token metadata for users.

### login_logs

Tracks login activity for auditing, monitoring, and analytics.

## Relationships

- A user can have many tokens and many login logs.
- A country can have many cities and locations.
- The ORM layer uses SQLAlchemy relationships to keep the model graph consistent.

## Migrations

Migrations are managed with Alembic under the versions folder. Use the following command to apply them:

```bash
alembic upgrade head
```

## Notes

- The database configuration is loaded from the environment through the settings module.
- The application expects an async PostgreSQL URL such as `postgresql+asyncpg://...`.
- The project currently uses UUID-based public identifiers alongside integer primary keys.
