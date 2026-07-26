# Project structure

This backend follows a layered architecture that separates API routes, application use cases, domain services, repositories, and database models.

## Main folders

- app/api: HTTP route definitions grouped by domain such as auth, user, locations, and settings.
- app/application: business logic organized into use cases and DTOs.
- app/core: shared infrastructure such as configuration, database, exceptions, logging, security, and Redis.
- app/deps: dependency injection helpers for services, repositories, auth, and database sessions.
- app/models: SQLAlchemy ORM models for the database schema.
- app/repositories: data-access layer for persistence and queries.
- app/services: shared domain services such as country, login log, token, storage, and user services.
- app/schemas: request and response schemas used by FastAPI.
- app/utils: helpers and decorators for cross-cutting concerns.
- tests: repository and integration-style tests.
- versions: Alembic migration files and configuration.

## Request flow

1. A request enters an API route under app/api.
2. The route delegates to an application use case in app/application/use_case.
3. The use case uses services and repositories to perform the work.
4. Results are returned through Pydantic schemas and response models.

## Architectural notes

- Routes stay thin and focus on HTTP concerns.
- Use cases contain the main business workflows.
- Repositories provide persistence operations and keep DB access centralized.
- Services handle reusable domain logic and external integrations.
- The core folder contains global configuration and infrastructure concerns.
