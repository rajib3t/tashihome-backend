# Project Development Phases & Roadmap

This document outlines the phased development roadmap for the **TashiHome Backend** platform. It reflects both implemented milestones and upcoming feature phases for a scalable, production-grade homestay and accommodation booking system.

---

## Roadmap at a Glance

| Phase | Domain | Status | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Core Foundation & Infrastructure** | ✅ **Completed** | FastAPI setup, Async SQLAlchemy 2.0, PostgreSQL, Redis, Alembic, S3 Storage, Event Bus |
| **Phase 2** | **Authentication, Users & Vendors** | ✅ **Completed** | JWT lifecycle, RBAC, Redis token blacklist, Login audit logs, Companies, Addresses |
| **Phase 3** | **Locations & Master Attributes** | ✅ **Completed** | Countries, Cities, Locations hierarchy, Facilities, Amenities, Room Types catalog |
| **Phase 4** | **Properties & Media Management** | ✅ **Completed** | Property listings CRUD, Multi-asset S3/CloudFront upload, Facilities/Amenities/Food options mapping |
| **Phase 5** | **Search, Availability & Booking Engine** | ✅ **Completed** | Date-range availability, Pricing engine, Booking state machine, Room blocks, Occupancy variable pricing, Row-level concurrency locks, Reservation hold TTL |
| **Phase 6** | **Payments, Invoicing & Payouts** | ✅ **Completed** | Razorpay gateway, Webhook signature verification, Idempotency engine, Refunds, Vendor bank accounts, RazorpayX payouts |
| **Phase 7** | **Reviews, Testimonials & Notifications** | ✅ **Completed** | Verified guest reviews, Testimonials moderation, Host applications with messaging, Socket.IO real-time notifications |
| **Phase 8** | **AI Concierge, MCP & Vector Search** | ✅ **Completed** | Bedrock Nova Lite / Gemini / OpenAI LLMs, MCP JSON-RPC/SSE & stdio server, S3 vector store & embeddings |
| **Phase 9** | **Production Resilience & Scaling** | 🔄 **Ongoing** | Pytest suites, Multi-worker Redis leader election, Method rate limiting, OpenTelemetry, Kubernetes manifests |

---

## Detailed Phase Breakdown

### Phase 1: Core Foundation & Infrastructure ✅
*Goal: Establish robust, clean architecture, database connectivity, asynchronous event distribution, and cloud storage.*

- [x] **FastAPI Application Core**:
  - Application lifecycle management with lifespan handlers.
  - Auto-discovering dynamic router loader (`app/api/router.py`) supporting route scoping (`admin`, `vendor`, `user`, `public`).
  - Standardized JSON response formatting and global exception handling.
- [x] **Database & Migrations**:
  - PostgreSQL connection via SQLAlchemy async engine (`postgresql+asyncpg`).
  - Migration workflow configured with Alembic (`versions/` and `alembic.ini`).
  - Base repository patterns (`BaseRepository`) with CRUD primitives.
- [x] **Caching & Session Storage**:
  - Redis connection pool for caching, rate limiting, and token revocation.
  - Distributed leader election mechanism for background cron/worker tasks.
- [x] **Event-Driven Architecture**:
  - In-process asynchronous event bus (`app/core/events.py`) with pub/sub event handlers (`app/events/`).
- [x] **Storage & CDN**:
  - S3-compatible object storage service (Local / AWS S3) for asset uploads.
  - CloudFront CDN integration for signed/cached URL resolution.

---

### Phase 2: Authentication, RBAC & Profile Management ✅
*Goal: Secure user identity, vendor onboarding, session auditing, and role-based access control.*

- [x] **Authentication & Token Management**:
  - User registration, email verification, and account activation flows.
  - Secure login with bcrypt password hashing and dual-token JWT (Access & Refresh tokens).
  - Password reset with time-bound verification tokens.
  - Token blacklisting and revocation in Redis on logout.
- [x] **Role-Based Access Control (RBAC)**:
  - Strict role enforcement for `admin`, `vendor`, and `user` via FastAPI dependency injection (`app/deps/`).
  - CSRF protection middleware for sensitive state-changing operations.
- [x] **Audit Logging & Device Tracking**:
  - Capture client IP, User-Agent, geo-resolved city/country, and JSONB device metadata in `login_logs`.
- [x] **User & Vendor Profiles**:
  - User profile management with avatar uploads.
  - Polymorphic address storage (`addresses`) supporting user and business addresses.
  - Vendor company registration (`companies`) and admin vendor management workflows.

---

### Phase 3: Locations & Master Catalog (Attributes) ✅
*Goal: Build the foundational geographic and catalog metadata required for property listings.*

- [x] **Geographical Hierarchy**:
  - Multi-tier structure: **Countries** -> **Cities** -> **Locations** (areas/neighborhoods).
  - Unique composite constraints (e.g., area names unique per city).
  - Admin management APIs with status toggles (`active`/`inactive`).
  - Public-facing APIs with city highlights, featured flags, and banner imagery.
- [x] **Master Attributes Catalog**:
  - **Facilities**: Property-wide amenities (e.g., Free Parking, Pool, Garden) with icon URLs.
  - **Amenities**: In-room features (e.g., Air Conditioning, Wi-Fi, Balcony) with icon URLs.
  - **Room Types**: Room categories with base capacity (e.g., Deluxe Suite, Standard Double).

---

### Phase 4: Properties & Media Management ✅
*Goal: Comprehensive listing management for vendors and administrators with rich media integration.*

- [x] **Property Listing Engine**:
  - Property model supporting various types (`hotel`, `homestay`, `villa`, `apartment`, `resort`, etc.).
  - Listing lifecycle statuses (`draft`, `active`, `inactive`, `archived`).
  - Geolocation coordinates (Latitude/Longitude), address, base price per night, and sale pricing.
  - Slug generation with vendor-scoped unique constraints.
- [x] **Property Associations**:
  - Property-to-RoomType mapping with custom configurations.
  - Property-to-Facility mapping with quantity and notes.
  - Property-to-Amenity mapping with custom notes.
  - Property Food & Dining options (e.g., Complimentary Breakfast).
- [x] **Media & Asset Pipeline**:
  - Multi-file asset uploader with metadata tagging (`image`, `video`, `document`).
  - Use-case placement classification (`gallery`, `feature`, `cover`).
  - Primary cover photo selection and display sort-ordering.
- [x] **Public & Vendor Interfaces**:
  - Public property listing with pagination, location filters, and detailed view.
  - Vendor property dashboard for creation, updates, and asset management.
  - Admin property oversight and moderation.
- [x] **Dynamic System Settings**:
  - Key-value configuration store (`settings`) for platform runtime parameters.

---

### Phase 5: Search, Availability & Booking Engine ✅
*Goal: High-performance search, real-time availability tracking, reservation holds, and booking lifecycle.*

- [x] **Search & Filtering Engine**:
  - Public search by destination/city/location, check-in/check-out dates, guest counts, and price ranges (`/api/v1/public/stay/*`).
  - Filter by property typology, facilities, amenities, and dining options.
  - Slug-based URL lookups and geo-location sorting.
- [x] **Availability Calendar & Dynamic Inventory**:
  - Real-time room inventory deduction accounting for active bookings (`pending`, `confirmed`, `checked_in`).
  - Property room blocks (`room_blocks`) for host blackout dates, maintenance holds, and private reservations.
  - Multi-occupancy variable pricing tiers (`property_room_type_prices`) per room category.
- [x] **Booking State Machine**:
  - Complete lifecycle: `pending` $\to$ `confirmed` $\to$ `checked_in` $\to$ `checked_out` $\to$ `cancelled` / `completed`.
  - Automated booking reference generator (e.g. `TSH-2026-XXXX`).
  - Guest details, guest count validation, and special requests handling.
- [x] **Concurrency & Double-Booking Protection**:
  - **Pessimistic Row-Level Locking (`SELECT ... FOR UPDATE`)**: Property row locks serialize simultaneous booking requests on the same property, ensuring atomic inventory verification and zero double bookings.
  - **Reservation Hold Expiry (`expires_at` / TTL)**: 15-minute hold window for unpaid pending reservations; `count_booked_units()` automatically excludes expired holds, releasing rooms back to inventory without manual intervention.
  - **Payment Flow Safeguards**: Expired reservations cannot generate Razorpay orders (`BOOKING_EXPIRED`); late payment captures on rebooked inventory automatically cancel the booking and initiate a refund request.
- [x] **Booking Administration**:
  - Admin booking oversight, filterable lists, status transition controls.
  - Vendor booking dashboard for checking reservations, guest records, and check-in status.
  - User booking dashboard for personal reservations and itinerary history.

---

### Phase 6: Payments, Invoicing & Payouts ✅
*Goal: Reliable payment gateway integration, transaction auditing, automated invoicing, and vendor payouts.*

- [x] **Payment Gateway Integration**:
  - Razorpay payment order generation, client checkout verification, and signature capture (`app/services/razorpay_service.py`).
  - Webhook processing with cryptographic HMAC SHA-256 signature verification (`X-Razorpay-Signature`).
  - Multi-currency support and payment status synchronization (`payments`).
- [x] **Idempotency Engine**:
  - Custom Redis-backed `IdempotencyMiddleware` supporting `Idempotency-Key` / `X-Idempotency-Key`.
  - Distributed in-flight request locking preventing race-condition double charges (returns HTTP 409).
  - SHA-256 request fingerprinting and 24-hour response caching with `Idempotent-Replay: true` header.
- [x] **Refunds & Cancellation Processing**:
  - Cancellation policy tier evaluation for automated refund calculations.
  - Refund requests workflow (`refund_requests`) with admin approval and Razorpay refund API execution.
- [x] **Host Banking & RazorpayX Payouts**:
  - Host bank account and UPI VPA registry (`vendor_bank_accounts`) with verification status.
  - Automated provisioning of RazorpayX Contacts (`vendor_razorpay_contacts`) and Fund Accounts (`vendor_razorpay_fund_accounts`).
  - Vendor payout settlement engine calculating gross revenue minus platform commission (`payouts`).
  - Disbursement execution via NEFT, RTGS, IMPS, and UPI modes.
- [x] **PDF Invoicing & Vouchers**:
  - Automated PDF invoice and booking voucher generation (`app/services/invoice_service.py`) with GST breakdown.

---

### Phase 7: Reviews, Testimonials, Host Requests & Real-Time Notifications ✅
*Goal: Social proof, host onboarding workflows, real-time alerts, and multi-channel communication.*

- [x] **Reviews & Ratings System**:
  - Verified guest reviews linked directly to completed bookings (`reviews`).
  - 1-to-5 star ratings with guest comments and host public replies.
  - Moderation states (`pending`, `published`, `hidden`, `flagged`, `rejected`).
- [x] **Platform Testimonials**:
  - Platform-wide endorsements submitted by guests or hosts (`testimonials`).
  - Admin review, approval, and homepage featuring flags.
- [x] **Host Onboarding & Inquiry Pipeline**:
  - Prospective host inquiry submission (`host_requests`) with property details and room estimates.
  - Admin review, status tracking (`pending`, `under_review`, `approved`, `rejected`, `converted`).
  - Internal and applicant messaging thread (`host_request_messages`).
  - One-click applicant conversion to active vendor account (`converted_user_id`).
- [x] **Real-Time Notification Engine**:
  - Persistent in-app notifications store (`notifications`).
  - Real-time WebSocket broadcasting via Socket.IO (`app/core/socket.py`).
  - Authenticated room-based channel isolation (`admin_notifications`, `vendor_{id}`, `user_{id}`).
- [x] **Transactional Email Service**:
  - Multi-provider email engine (`app/services/email_service.py`) supporting SMTP, Mailgun, Brevo, and Mock modes.
  - HTML email templates rendered via Jinja2 for account verification, password reset, and booking milestones.

---

### Phase 8: AI Concierge, Model Context Protocol (MCP) & Vector Search ✅
*Goal: Conversational travel concierge, standardized MCP integration, and semantic homestay search.*

- [x] **Multi-Provider LLM Integration**:
  - Pluggable AI engine supporting Amazon Bedrock (Nova Lite, Titan), Google Gemini (`gemini-1.5-flash`), and OpenAI.
  - Conversational intent detection, entity extraction, and multi-turn dialogue management.
  - Streaming responses (`/api/v1/public/assistant/chat/stream`) using Server-Sent Events (SSE).
- [x] **Model Context Protocol (MCP) Server**:
  - Standardized MCP server implementation (`app/mcp/`) compliant with the Model Context Protocol specification.
  - JSON-RPC 2.0 endpoint (`/api/v1/public/mcp/rpc`) and persistent SSE stream (`/api/v1/public/mcp/sse`).
  - Standalone stdio MCP runner (`scripts/mcp_server.py`) for external desktop clients (Claude Desktop, Cursor).
  - Comprehensive tool suite (`search_homestays`, `check_availability`, `get_property_details`, `get_cancellation_policies`, `create_booking_reservation`).
  - Standardized prompts and dynamic resources (`homestay://catalog`, `homestay://destinations`).
- [x] **Vector Embeddings & Semantic Search**:
  - Embedding generation pipeline (`text-embedding-004`, `amazon.titan-embed-text-v2:0`).
  - Cosine similarity vector search engine (`app/services/vector_search_service.py`).
  - Persistent vector index storage in Amazon S3 (`tashihome-vector`).
  - Natural language stay search API (`/api/v1/public/assistant/semantic-search`).
  - Embedding synchronization CLI tool (`scripts/sync_embeddings.py`).
- [x] **Strict Security & Privacy**:
  - Zero internal integer database ID leakage (exclusive UUIDv4 usage across all tools and schemas).
  - Defensive parameter bounds, Pydantic validation, and read/write tool separation.

---

### Phase 9: Production Resilience, Hardening & Enterprise Scaling 🔄
*Goal: Maximize reliability, observability, distributed worker safety, and CI/CD automation.*

- [x] **Distributed Multi-Worker Safety**:
  - Continuous Redis leader election (`RedisLeaderElector`) ensuring only a single elected leader runs background jobs and event subscribers.
  - Decoupled deployment support (run scheduler embedded in web leader OR as isolated daemon `scripts/run_scheduler.py`).
  - Redis distributed locking preventing overlapping cron job executions.
- [x] **Pre-Aggregated Public Statistics Engine**:
  - Dedicated `public_stats` table updated asynchronously by APScheduler to serve landing page stats in $O(1)$ time without joins.
  - CLI job runner (`scripts/run_job.py`) for on-demand job inspection and manual execution.
- [x] **Defensive Rate Limiting & Cooldown**:
  - Method-specific sliding-window rate limiter (GET, POST, PUT, PATCH, DELETE) with 1-hour abusive IP cooldown lockout (`app/core/rate_limiter.py`).
- [x] **Automated Testing Suite**:
  - Unit and integration tests (`pytest`, `pytest-asyncio`) for use cases, repositories, rate limiting, idempotency, MCP tools, and vector search.
- [ ] **Observability & Telemetry**:
  - Prometheus metrics exporter for request latency, error counts, and DB connection pool saturation.
  - OpenTelemetry distributed tracing across HTTP, Redis, and PostgreSQL calls.
  - Centralized structured JSON logging and Sentry APM integration.
- [ ] **DevOps & Cloud Orchestration**:
  - Multi-stage production Dockerfile and Docker Compose environment.
  - Kubernetes deployment manifests (Web Deployment, Background Worker StatefulSet, HPA).
  - GitHub Actions CI/CD workflows for automated linting, test runs, migration dry-runs, and staging deployments.

