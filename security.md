# Security guide

This document outlines the main security considerations for the TashiHome backend and the practices that should be followed while developing and deploying it.

## Authentication and authorization

- JWT-based authentication is used for access and refresh tokens.
- Token secrets and signing algorithms should be kept in environment variables and never committed to source control.
- Role-based access should be enforced at the route and use-case level.
- Sensitive operations should require authenticated users and appropriate permissions.

## Password handling

- Passwords should be hashed using a strong password hashing algorithm.
- Plaintext passwords must never be stored, logged, or returned in API responses.
- Password reset and verification flows should use short-lived signed tokens.

## Configuration and secrets

- Environment files such as .env should be treated as secret material.
- Production credentials, database URLs, Redis credentials, and JWT secrets should be injected through the deployment environment.
- Avoid exposing secrets in logs, stack traces, or exception payloads.

## Input validation

- FastAPI request validation should be used for all incoming data.
- Pydantic schemas should define allowed types, lengths, and required fields.
- Reject unexpected payloads and malformed data early.

## Database security

- Use strong database credentials and restrict network access.
- Apply migrations carefully and review schema changes before deployment.
- Prefer parameterized queries and ORM usage to reduce SQL injection risk.

## API security

- Enable CORS only for trusted origins.
- Use HTTPS in production.
- Consider rate limiting and abuse protection for public endpoints.
- Return minimal error detail to clients to avoid leaking internal implementation details.

## Dependency and environment hygiene

- Keep dependencies updated and review them regularly.
- Run dependency audits and security scans as part of the development workflow.
- Use isolated environments for development, testing, and production.

## Operational recommendations

- Enable logging for authentication and security-relevant events.
- Monitor failed login attempts, invalid tokens, and abnormal traffic patterns.
- Use infrastructure protections such as firewalls, secrets managers, and managed database services where possible.
