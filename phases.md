# Project Development Phases & Roadmap

This document outlines the phased development roadmap for the **TashiHome Backend** platform. It reflects both implemented milestones and upcoming feature phases for a scalable, production-grade homestay and accommodation booking system.

---

## Roadmap at a Glance

| Phase | Domain | Status | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Core Foundation & Infrastructure** | ✅ **Completed** | FastAPI setup, Async SQLAlchemy, PostgreSQL, Redis, Alembic, S3 Storage, Event Bus |
| **Phase 2** | **Authentication, Users & Vendors** | ✅ **Completed** | JWT lifecycle, RBAC, Redis token blacklist, Login audit logs, Companies, Addresses |
| **Phase 3** | **Locations & Master Attributes** | ✅ **Completed** | Countries, Cities, Locations hierarchy, Facilities, Amenities, Room Types catalog |
| **Phase 4** | **Properties & Media Management** | ✅ **Completed** | Property listings CRUD, Multi-asset S3/CloudFront upload, Facilities/Amenities/Food options mapping |
| **Phase 5** | **Search, Availability & Bookings** | 🔄 **In Progress** | Date-range availability, Pricing engine, Booking state machine, Redis reservation locks |
| **Phase 6** | **Payments, Invoicing & Payouts** | ⏳ **Planned** | Payment gateways (Razorpay/Stripe), Webhook handling, Refunds, Vendor payouts |
| **Phase 7** | **Reviews, Wishlists & Communication** | ⏳ **Planned** | Guest reviews & ratings, Wishlist/favorites, Host-guest messaging, Transactional emails |
| **Phase 8** | **Observability, Hardening & Deployment**| 🔄 **Ongoing** | Unit/integration test suites, OpenTelemetry/Prometheus, CI/CD, Containerization |

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

### Phase 5: Search, Availability & Booking Engine 🔄
*Goal: High-performance search, real-time availability tracking, reservation holds, and booking lifecycle.*

- [ ] **Search & Filtering Engine**:
  - Public search by destination/city/location, check-in/check-out dates, guest counts, and price ranges.
  - Filter by property type, facilities, amenities, and food options.
  - Geospatial radius search based on coordinates.
- [ ] **Availability Calendar & Dynamic Pricing**:
  - Day-by-day room inventory and availability tracking.
  - Seasonal pricing, weekend markups, custom date-based discounts, and minimum stay rules.
- [ ] **Booking State Machine**:
  - Lifecycle: `pending` -> `confirmed` -> `checked_in` -> `checked_out` -> `cancelled` / `refunded`.
  - Redis-backed distributed locks for temporary inventory reservation holds (15-minute hold during checkout).
  - Guest details, guest count verification, and special requests handling.
- [ ] **Vendor Booking Dashboard**:
  - Vendor reservation calendar, booking approval/rejection, check-in verification.
  - Guest communication and cancellation policy enforcement.

---

### Phase 6: Payments, Invoicing & Payouts ⏳
*Goal: Reliable payment gateway integration, transaction auditing, automated invoicing, and vendor payouts.*

- [ ] **Payment Gateway Integration**:
  - Multi-gateway support (Stripe, Razorpay, PhonePe).
  - Payment intent creation, customer checkout sessions, and 3D Secure verification.
- [ ] **Webhooks & Idempotency**:
  - Resilient webhook processing with cryptographic signature verification.
  - Idempotent transaction processing to prevent duplicate charges or double bookings.
- [ ] **Refunds & Cancellation Processing**:
  - Automated refund calculation based on property cancellation policies (e.g. Free cancellation up to 48 hours).
  - Partial refunds and penalty deductions.
- [ ] **Vendor Commission & Payouts**:
  - Platform commission fee deduction per booking.
  - Vendor ledger, wallet balance, and payout disbursement tracking.
  - Automated PDF invoice and booking voucher generation.

---

### Phase 7: Reviews, Wishlists & Engagement ⏳
*Goal: Social proof, traveler retention, wishlist collections, and multi-channel notifications.*

- [ ] **Reviews & Ratings System**:
  - Verified-stay reviews only (guests who have completed their stay).
  - Multi-criteria ratings (Cleanliness, Location, Service, Value for Money, Accuracy).
  - Vendor response to reviews and admin moderation queue.
- [ ] **Wishlists & Saved Properties**:
  - Traveler wishlist collections and favorites toggle.
- [ ] **Transactional Notification System**:
  - Automated transactional emails (HTML templates via Jinja2) for booking confirmations, cancellations, and invoices.
  - SMS & WhatsApp alerts for critical booking milestones.
  - In-app notification center for users and vendors.
- [ ] **Guest-Host Messaging**:
  - In-platform direct messaging between confirmed guests and property hosts.

---

### Phase 8: Production Hardening, Observability & Scaling 🔄
*Goal: Maximize reliability, security compliance, performance under high load, and CI/CD automation.*

- [ ] **Testing & Quality Assurance**:
  - End-to-end integration tests for checkout, booking, and payment flows.
  - Repository and use case unit test suites (`pytest`, `pytest-asyncio`).
  - Stress and concurrency testing for inventory locking under flash sales.
- [ ] **Monitoring & Observability**:
  - Prometheus metrics endpoint for request latency, error rates, and DB pool stats.
  - Structured JSON logging and Sentry integration for real-time error tracking.
  - OpenTelemetry distributed tracing.
- [ ] **Security & Compliance**:
  - OWASP Top 10 hardening (SQLi prevention, XSS mitigation, rate-limiting per IP/User).
  - PII data encryption and GDPR-compliant data export/deletion requests.
- [ ] **DevOps & Infrastructure**:
  - Production Dockerfile with multi-stage builds and minimal image size.
  - Docker Compose for local full-stack replication (Backend, PostgreSQL, Redis, MinIO/LocalStack).
  - GitHub Actions CI/CD for automated linting, testing, migration checks, and cloud deployments.
