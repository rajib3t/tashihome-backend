# Codebase Structure & Architecture Reference

This backend is built on a **Layered Clean Architecture** that enforces a strict separation of concerns across API routing, application workflows, domain services, data persistence, real-time communication, and external integrations.

---

## High-Level Architecture Overview

```
                                 [ Client Requests ]
                               (Web, Mobile, External)
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                              Middleware Pipeline                                  |
|     IdempotencyMiddleware (Redis)      |      RateLimitMiddleware (Method Sliding) |
|     CORSMiddleware                     |      TrustedHostMiddleware                |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                              API Routing Layer                                    |
|                      app/api/router.py (Auto-Discovery)                           |
|       /admin/*         |        /vendor/*        |       /user/*       |  /public/*   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           Application Use Cases Layer                             |
|                              app/application/use_case                             |
|              Orchestrates business workflows, transactions, and DTOs              |
+--------------------+--------------------+--------------------+--------------------+
                     |                    |                    |
                     v                    v                    v
+-------------------------+  +-------------------------+  +-------------------------+
|     Domain Services     |  |   Repositories (Data)   |  |   Real-Time / Events    |
|      app/services       |  |    app/repositories     |  |   app/events, Socket.IO |
| Razorpay, Bedrock/Gemini|  |  SQLAlchemy 2.0 Async   |  | In-Process Event Bus,   |
| Vector Search, Emails   |  |  PostgreSQL Statements  |  | Redis Leader Election   |
+-------------------------+  +-------------------------+  +-------------------------+
                     |                    |
                     v                    v
+-----------------------------------------------------------------------------------+
|                              Persistence & Infrastructure                         |
|      PostgreSQL (Asyncpg)   |   Redis (Cache/Locks)   |   AWS S3 (Assets/Vectors) |
+-----------------------------------------------------------------------------------+
```

---

## Directory Map & Package Breakdown

### 1. `app/api/` — API Routing & Controllers
All HTTP endpoints are organized by domain and automatically registered via dynamic discovery in `app/api/router.py`.

- **Auto-Discovery Loader (`app/api/router.py`)**: Traverses `app/api/`, imports any module ending in `_route.py`, and scopes it with the appropriate URL prefix:
  - `/api/v1/admin/*` — Administrative management and moderation.
  - `/api/v1/vendor/*` — Homestay host listings, bookings, room blocks, and calendar.
  - `/api/v1/user/*` — Authenticated guest operations, personal bookings, reviews, testimonials, host inquiries (`become_host_route.py`).
  - `/api/v1/public/*` — Unauthenticated consumer endpoints:
    - `/public/stay/*` & `/public/property/*` — Property discovery, filters, slug lookups.
    - `/public/assistant/*` — Conversational AI concierge, streaming chat, semantic vector search, checkout.
    - `/public/mcp/*` — Model Context Protocol JSON-RPC 2.0 (`/mcp/rpc`) and SSE (`/mcp/sse`).
    - `/public/city/*` — Destination discovery and featured cities.
    - `/public/stat/*` — Pre-aggregated platform overview statistics.
    - `/public/host-request/*` — Prospective host registration inquiries.
  - Core cross-cutting routes:
    - `auth/auth_route.py` — Login, registration, token refresh, password resets.
    - `profile_route.py` — User profile, password management, avatar upload.
    - `notification_route.py` — In-app notification center, unread counters, mark-as-read.
    - `asset_route.py` — Direct upload pre-signed URLs and media management.

### 2. `app/application/` — Business Use Cases & DTOs
Contains pure application logic isolated from HTTP transport details.

- **`app/application/use_case/`**:
  - `admin/` — Admin vendor onboarding, payout approvals, staff accounts, tax settings, content moderation.
  - `vendor/` — Vendor homestay registration, property updates, room unit management, room blocks.
  - `user/` — Booking creations, cancellation requests, review submissions, testimonials.
  - `auth/` — Registration, login verification, token refreshing, password resets.
  - `public/` — Property search, slug resolution, destination highlights.
- **`app/application/dto/`**: Data Transfer Objects defining typed inputs and outputs between routes and use cases.

### 3. `app/core/` — Infrastructure & Platform Primitives
Foundational system components:

- **`config.py`**: Centralized Pydantic Settings (`Settings`) managing environment variables (`.env`).
- **`database.py`**: Async SQLAlchemy 2.0 engine, `async_session_factory`, and declarative `Base`.
- **`redis.py`**: Asynchronous Redis connection pool client (`redis_client`).
- **`leader_election.py`**: `RedisLeaderElector` providing continuous leader election so only a single elected Gunicorn/Uvicorn worker executes background schedulers and event subscribers.
- **`idempotency.py`**: Enterprise Redis-backed `IdempotencyMiddleware` supporting `Idempotency-Key` / `X-Idempotency-Key`, concurrent in-flight locking (HTTP 409), and 24-hour response caching.
- **`rate_limiter.py`**: Sliding-window `RateLimitMiddleware` with method-specific limits (GET, POST, PUT, PATCH, DELETE) and 1-hour abusive IP cooldown penalties.
- **`csrf.py`**: Double-Submit Cookie CSRF verification middleware.
- **`security.py`**: JWT token creation, decoding, password hashing (`pwdlib` / Argon2id / bcrypt), and timing-safe comparisons.
- **`socket.py`**: Python-SocketIO ASGI server (`sio`) with authenticated room management (`admin_notifications`, `vendor_{id}`, `user_{id}`).
- **`logging_config.py`**: Structured application logging configuration.
- **`exceptions.py`**: Domain application exceptions (`AppException`) and HTTP error handlers.

### 4. `app/deps/` — FastAPI Dependency Injection
Provides modular dependencies for route handlers:

- Database session injection (`get_db`).
- Authentication and token resolution (`get_current_user`, `get_current_active_user`).
- Role-based access enforcement (`require_admin`, `require_vendor`, `require_staff`).
- Repository and Service factory bindings.

### 5. `app/events/` — Event-Driven Architecture
- **`event_bus.py`**: In-process asynchronous pub/sub event bus (`EventBus`).
- **`subscriber.py`**: Event loop subscriber running on the elected worker leader.
- **`handlers/`**: Event consumers (e.g. `notification_handler.py` translating domain events into persistent notifications and real-time Socket.IO broadcasts).

### 6. `app/mcp/` — Model Context Protocol (MCP) Server
Standardized implementation of the Model Context Protocol:

- **`protocol.py`**: JSON-RPC 2.0 protocol definitions, error codes, and message serializers.
- **`server.py`**: `TashiHomeMCPServer` coordinating tool dispatch, resource queries, and prompts.
- **`tools.py`**: Comprehensive tool schemas and executors (`search_homestays`, `check_availability`, `get_property_details`, `get_cancellation_policies`, `create_booking_reservation`, `calculate_pricing`).
- **`resources.py`**: Dynamic resource providers (`homestay://catalog`, `homestay://destinations`).
- **`prompts.py`**: Reusable MCP prompt templates for travel recommendations and itinerary planning.

### 7. `app/models/` — SQLAlchemy 2.0 ORM Models
Declarative database entity models mapping to all 36 PostgreSQL tables (see [database.md](database.md) for full catalog).

### 8. `app/repositories/` — Data Access Layer
Encapsulates all SQL query logic, filters, pagination, and database joins using SQLAlchemy 2.0 `select()` constructs:

- `base_repository.py` — Generic CRUD primitives.
- Domain repositories: `property_repository.py`, `booking_repository.py`, `user_repository.py`, `payout_repository.py`, `review_repository.py`, `room_block_repository.py`, `notification_repository.py`, etc.

### 9. `app/schedulers/` — Background Jobs & APScheduler
- **`base.py`**: `BaseJob` abstract class with automatic session management and Redis distributed locking.
- **`registry.py`**: Automatic decorator-driven job registry (`@register_job`).
- **`manager.py`**: `SchedulerManager` managing the APScheduler `AsyncIOScheduler` instance.
- **`jobs/public_stats_job.py`**: Periodically pre-aggregates total homestays, destinations, average ratings, and review counts into `public_stats`.

### 10. `app/schemas/` — Pydantic Request & Response Models
Data schemas enforcing input validation, typing, and serialization for API boundaries:

- `auth_schema.py`, `user_schema.py`, `property_schema.py`, `booking_schema.py`, `payment_schema.py`, `payout_schema.py`, `review_schema.py`, `host_request_schema.py`, `notification_schema.py`, etc.

### 11. `app/services/` — Domain Services & Integrations
Reusable business services:

- **`assistant_service.py`**: Conversational AI concierge with multi-provider LLM orchestration (Bedrock Nova Lite, Gemini, OpenAI) and tool calling.
- **`vector_search_service.py`**: Cosine similarity vector search over homestay embeddings.
- **`embedding_service.py`**: Text embedding generation (`text-embedding-004`, `amazon.titan-embed-text-v2:0`).
- **`razorpay_service.py`**: Razorpay Orders, payment capture, webhook signature verification, and RazorpayX Payouts.
- **`notification_service.py`**: Notification creation, unread count aggregation, and real-time Socket.IO emission.
- **`invoice_service.py`**: Dynamic PDF invoice and booking voucher generation.
- **`storage_service.py`**: AWS S3 / MinIO asset uploading, presigned URLs, and file deletion.
- **`cloudfront_service.py`**: RSA private-key signed cookies and signed URLs for private asset distribution.
- **`email_service.py`**: Multi-provider email dispatch (SMTP, Mailgun, Brevo, Mock) with Jinja2 templates.

### 12. `scripts/` — Standalone CLI Utilities
- **`mcp_server.py`**: Standalone stdio MCP server runner for desktop tools (Claude Desktop, Cursor).
- **`run_job.py`**: CLI utility to list and execute background scheduled jobs on demand.
- **`run_scheduler.py`**: Dedicated background worker daemon for decoupled production deployments.
- **`sync_embeddings.py`**: Indexes homestay descriptions into vector embeddings and uploads to S3.
- **`create_admin.py`**: Initial super administrator provisioning script.
- **`populate_slugs.py`**: Backfills URL slugs for properties, cities, and locations.

---

## Request & Data Flows

### 1. Standard REST Request Flow
```
Client
  │  (HTTP Request)
  ▼
Middleware Pipeline (Idempotency, Rate Limit, CORS, TrustedHost)
  │
  ▼
app/api/router.py ──► Route Controller (e.g. app/api/admin/property/property_route.py)
                        │  (Dependencies: get_db, require_admin)
                        ▼
                      Application Use Case (app/application/use_case/...)
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
    Domain Service                Repository (SQLAlchemy 2.0)
  (app/services/...)            (app/repositories/...)
         │                             │
         ▼                             ▼
   External APIs / S3            PostgreSQL Database (Asyncpg)
         │                             │
         └──────────────┬──────────────┘
                        │
                        ▼
           Pydantic Schema Serialization
                        │
                        ▼
Client ◄── (HTTP 200/201 JSON Response)
```

---

### 2. Idempotent State-Modifying Flow
```
Client Request (with `Idempotency-Key: <UUID>`)
  │
  ▼
IdempotencyMiddleware
  │
  ├──► Check Redis Lock: `idempotency:lock:<Fingerprint>`
  │     ├── Lock active? ──► Return HTTP 409 Conflict (Request already in-flight)
  │     └── Lock acquired (30s TTL)
  │
  ├──► Check Redis Cache: `idempotency:<Fingerprint>`
  │     └── Found in cache? ──► Return Cached JSON Response + `Idempotent-Replay: true`
  │
  ├──► Execute Route Handler & Commit DB Transaction
  │
  ├──► Save Response in Redis (24-Hour TTL)
  └──► Release Lock ──► Return Response to Client
```

---

### 3. Real-Time Notification & Event Flow
```
Domain Action (e.g. Booking Confirmed)
  │
  ▼
app/events/event_bus.py (Publish Event)
  │
  ▼
Notification Handler (app/events/handlers/notification_handler.py)
  │
  ├──► NotificationService: Persist record to `notifications` table (PostgreSQL)
  │
  └──► Socket.IO Manager (app/core/socket.py)
        │
        ├── Emit to `user_{guest_id}`: `new_notification`
        ├── Emit to `vendor_{vendor_id}`: `new_notification`
        └── Emit to `admin_notifications`: `new_notification`
```

---

### 4. AI Concierge & Model Context Protocol (MCP) Flow
```
User Chat Request (`POST /api/v1/public/assistant/chat`)
  │
  ▼
AssistantService (app/services/assistant_service.py)
  │
  ├──► Intent Detection & Context Assembly
  │
  ├──► LLM Provider (Bedrock Nova Lite / Gemini / OpenAI)
  │     └── LLM requests Tool Call: e.g. `search_homestays(city="Thimphu")`
  │
  ├──► MCP Tool Executor (app/mcp/tools.py)
  │     ├── Validate Arguments via Pydantic Schema
  │     ├── Query PropertyRepository & RoomBlockRepository
  │     └── Format Tool Result (Enforcing Opaque UUID strings only)
  │
  ├──► Feed Tool Output back to LLM
  └──► Return Conversational Markdown + Homestay Cards (or SSE Stream)
```

---

### 5. Multi-Worker Scheduled Task & Leader Election Flow
```
Gunicorn Cluster (Workers 1, 2, 3, 4)
  │
  ▼
All Workers attempt Redis Lock: `SET leader_lock <worker_id> NX EX 15`
  │
  ├── Worker 1 succeeds ──► Elected LEADER
  │     ├── Start Event Bus Subscriber (`start_event_subscriber()`)
  │     └── Start Background Scheduler (`start_scheduler()`)
  │           └── APScheduler executes `PublicStatsJob` under distributed lock
  │                 └── Pre-aggregates stats into `public_stats` table
  │
  └── Workers 2, 3, 4 ──► STANDBY
        └── Serve incoming HTTP requests with zero background task overhead
        └── Heartbeat loop monitors leader lock; auto-elects new leader on failure
```

---

## Architectural Principles & Invariants

1. **Thin Controllers**: Route handlers only handle HTTP request parsing, dependency injection, and delegating to application use cases.
2. **Rich Domain Workflows**: Complex business transactions (e.g. booking creation, cancellation calculations, payout distributions) live within use cases and domain services.
3. **Centralized Persistence**: Direct SQL queries or ORM session interactions never occur in route files; all persistence is routed through `app/repositories/`.
4. **Zero Internal ID Exposure**: The database integer primary keys (`BigInteger`) are strictly internal. Client APIs, URLs, MCP tools, and notifications exclusively consume and produce public UUIDs (`public_id`).
5. **Decoupled Deployments**: Schedulers and workers can run embedded inside the web process (via leader election) or isolated as independent microservice containers (`python scripts/run_scheduler.py`).

