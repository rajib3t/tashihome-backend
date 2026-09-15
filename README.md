# TashiHome Backend

TashiHome Backend is a high-performance, enterprise-grade FastAPI application powering the TashiHome homestay and accommodation platform. It features clean layered architecture, real-time WebSocket communication via Socket.IO, an AI Concierge with Model Context Protocol (MCP) server integration, vector semantic search, Razorpay payments and RazorpayX payouts, an enterprise Redis idempotency engine, method-specific rate limiting, pre-aggregated analytics, and a multi-worker safe scheduled tasks framework.

---

## Architecture Highlights

- **Layered Clean Architecture**: Strict separation of concerns — API Routes $\to$ Application Use Cases $\to$ Domain Services $\to$ Repositories $\to$ Database Models.
- **Real-Time Communication (Socket.IO ASGI)**: Seamlessly mounted Socket.IO server handling instant event broadcasts, unread notification counters, and room-scoped messaging (`user_{id}`, `vendor_{id}`, `admin_notifications`).
- **AI Concierge & Model Context Protocol (MCP)**:
  - Multi-provider LLM support: Amazon Bedrock (Nova Lite, Titan), Google Gemini (`gemini-1.5-flash`), and OpenAI.
  - Conversational chat with tool calling and progressive Server-Sent Events (SSE) token streaming (`/api/v1/public/assistant/chat/stream`).
  - Full MCP standard compliance with JSON-RPC 2.0 (`/api/v1/public/mcp/rpc`), SSE stream (`/api/v1/public/mcp/sse`), and standalone stdio CLI runner (`scripts/mcp_server.py`) for Claude Desktop and Cursor.
- **Vector Semantic Search**: Cosine similarity search over text embeddings (`text-embedding-004`, `amazon.titan-embed-text-v2:0`) stored in Amazon S3 (`tashihome-vector`) for vibe-based and natural language stay discovery.
- **Financial Workflows, Invoicing & Payouts**:
  - Razorpay payment order generation, client signature capture, and HMAC SHA-256 webhook verification.
  - Automated vendor payouts via RazorpayX Contacts & Fund Accounts linked to host bank accounts (`vendor_bank_accounts`).
  - Itemized tax & GST engine (`taxes`), sequential monthly tax invoice numbering (`invoice_number`), and automated PDF invoices/booking vouchers generation.
- **Multi-User Booking Concurrency & Double-Booking Protection**:
  - **Pessimistic Row-Level Locking (`SELECT ... FOR UPDATE`)**: Property rows are locked during booking creation, serializing concurrent checkouts so inventory checks are atomic and double-bookings are prevented even under high concurrency.
  - **Reservation Hold Expiry (`expires_at` / TTL)**: Unpaid `pending` bookings automatically hold room inventory for 15 minutes (`BOOKING_HOLD_MINUTES = 15`), automatically releasing dates back to other guests if checkout is abandoned.
  - **Payment Reconciliation Safeguards**: Razorpay payment verification re-checks availability on expired reservations, preventing overbooking and issuing automated refunds if dates were already rebooked.
- **Dynamic Platform Settings & Media Engine**:
  - Key-value platform configuration store (`settings`) with multi-file asset uploader (app logo, white logo, favicon, OG meta image, coming-soon video) with automated WebP compression and file size caps.
  - Automated replacement garbage collection in S3 to prevent orphaned storage bloat.
  - Dynamic maintenance and Coming Soon mode toggling with public payload gating.
- **Geographical Slug Routing**: URL-friendly, collision-safe slug routing for countries, cities, and neighborhood locations with composite unique constraints.
- **Enterprise Idempotency Engine (`app/core/idempotency.py`)**: Custom Redis-backed middleware supporting `Idempotency-Key` / `X-Idempotency-Key`, concurrent in-flight locking (HTTP 409 prevention of duplicate charges), and 24-hour response caching (`Idempotent-Replay: true`).
- **Advanced Rate Limiting (`app/core/rate_limiter.py`)**: Method-specific sliding-window rate limits (GET 120/min, POST 30/min, PUT 30/min, PATCH 30/min, DELETE 20/min) with automatic 1-hour abusive IP cooldown lockouts.
- **Pre-Aggregated Public Stats**: Dedicated `public_stats` table updated asynchronously by background jobs to serve homepage statistics in $O(1)$ time with zero multi-table joins.
- **Multi-Worker Safety (Redis Leader Election)**: Only the single elected Gunicorn worker runs the background scheduler and event subscriber. Standby workers serve HTTP traffic with zero task overhead.
- **Decoupled Production Deployments**: Supports running scheduled tasks embedded in the web leader OR as a dedicated isolated worker container (`python scripts/run_scheduler.py`).

---

## Tech Stack

| Category | Technology |
| :--- | :--- |
| **Runtime & Language** | Python 3.14+ |
| **Web Framework & Server** | FastAPI, Uvicorn, Gunicorn (async workers) |
| **Database & ORM** | PostgreSQL 14+, SQLAlchemy 2.0 (Async), `asyncpg` async driver, `psycopg2` sync driver (Alembic) |
| **Cache & Message Broker** | Redis 6.2+ (Connection pool, distributed locks, token blacklisting) |
| **Real-Time Communication**| Python-SocketIO (ASGI mounted) |
| **Task Scheduler** | APScheduler 3.x (`AsyncIOScheduler`) with Redis distributed locking |
| **Cloud Storage & CDN** | AWS S3 / MinIO, Amazon CloudFront (RSA private key signed cookies/URLs) |
| **Payments & Payouts** | Razorpay Payment Gateway, RazorpayX Banking & Payout APIs |
| **AI & LLM Orchestration** | Amazon Bedrock (Nova Lite, Titan), Google Gemini, OpenAI, MCP SDK |
| **Settings & Validation** | Pydantic Settings v2, Pydantic v2 schemas |

---

## Prerequisites

- **Python**: `>= 3.14`
- **PostgreSQL**: `>= 14`
- **Redis**: `>= 6.2`
- Package manager: [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

---

## Getting Started (Development Setup)

### 1. Clone & Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using standard `pip`:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure Environment Variables

Create your local `.env` file:
```bash
cp .env.example .env
```

Ensure the key settings in `.env` match your local environment:
```env
APP_NAME=TashiHome
ENV=development
DEBUG=true
PORT=8020

# Database & Redis
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tashihome
REDIS_HOST=localhost
REDIS_PORT=6379

# Authentication
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting & Idempotency
RATE_LIMIT_ENABLED=true
IDEMPOTENCY_ENABLED=true

# Payments & Bookings
PAYMENT_ENABLED=true
BOOKING_HOLD_MINUTES=15
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...

# Background Scheduler
ENABLE_SCHEDULER=true
PUBLIC_STATS_UPDATE_INTERVAL_MINUTES=15

# AI Assistant & MCP
AI_ENABLED=true
AI_PROVIDER=gemini           # "bedrock", "gemini", "openai", "mock"
GEMINI_API_KEY=...
AI_MODEL=gemini-1.5-flash

# Vector Semantic Search
VECTOR_SEARCH_ENABLED=true
EMBEDDING_PROVIDER=gemini    # "bedrock", "gemini", "openai"
VECTOR_S3_BUCKET=tashihome-vector
```

### 3. Run Database Migrations

Apply all schema migrations up to the latest head:
```bash
alembic upgrade head
```

### 4. Provision Super Admin Account

Create your initial super admin account:
```bash
python scripts/create_admin.py --email admin@tashihomes.in --password AdminSecurePassword123! --phone +919876543210
```

### 5. Synchronize Vector Embeddings (Optional)

Index homestay listings into vector embeddings and sync to the vector index:
```bash
python scripts/sync_embeddings.py
```

### 6. Start Application in Development Mode

Run with auto-reload:
```bash
uvicorn main:app --reload --port 8020
```
Or directly:
```bash
python main.py
```

- **Swagger UI Interactive Docs**: [http://localhost:8020/docs](http://localhost:8020/docs)
- **Health Check**: [http://localhost:8020/](http://localhost:8020/)
- **Public Stats**: [http://localhost:8020/api/v1/public/stat](http://localhost:8020/api/v1/public/stat)
- **Socket.IO Endpoint**: `ws://localhost:8020/socket.io/`

---

## AI Concierge & Model Context Protocol (MCP)

TashiHome features an integrated AI Travel Concierge and a full implementation of the **Model Context Protocol (MCP)**.

### Key AI Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/public/assistant/chat` | Conversational assistant with multi-tool calling |
| `POST` | `/api/v1/public/assistant/chat/stream` | Streaming assistant replies via Server-Sent Events (SSE) |
| `POST` | `/api/v1/public/assistant/semantic-search`| Natural language / vibe-based vector stay search |
| `POST` | `/api/v1/public/assistant/checkout` | Direct AI checkout with auto-registration |
| `POST` | `/api/v1/public/mcp/rpc` | JSON-RPC 2.0 MCP endpoint |
| `GET` | `/api/v1/public/mcp/sse` | Persistent Server-Sent Events stream for MCP |
| `GET` | `/api/v1/public/mcp/tools` | List all available MCP tool schemas |

### Connecting MCP Desktop Clients (Claude Desktop / Cursor)

To connect Claude Desktop or Cursor to TashiHome tools and resources, add this configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tashihome": {
      "command": "/var/www/tashihome-backend/.venv/bin/python",
      "args": ["scripts/mcp_server.py"],
      "cwd": "/var/www/tashihome-backend",
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/tashihome",
        "REDIS_HOST": "localhost"
      }
    }
  }
}
```

---

## Production Deployment Guide

### Strategy A: Multi-Worker Web Server with Built-in Leader Election (Standard)

In standard production setups, run multiple Uvicorn workers behind Gunicorn. Thanks to the built-in `RedisLeaderElector`, **only ONE worker is elected leader** and runs the background scheduler and event subscriber. Standby workers only process incoming HTTP requests.

```bash
# Set production environment
export ENV=production
export DEBUG=false
export ENABLE_SCHEDULER=true

# Start Gunicorn with 4 async Uvicorn workers
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8020 \
  --access-logfile - \
  --error-logfile - \
  --graceful-timeout 30 \
  --timeout 60
```

> **How it works under the hood**:
> - Worker 1 acquires the Redis leadership lock $\to$ starts `start_event_subscriber()` and `start_scheduler()`.
> - Workers 2, 3, 4 are standbys $\to$ handle HTTP and Socket.IO traffic only.
> - If Worker 1 restarts or crashes, Worker 2 automatically takes over leadership within seconds.

---

### Strategy B: Decoupled Enterprise Deployment (High Traffic / Kubernetes)

For high-traffic or microservices architectures, isolate HTTP API servers from background task processing:

#### 1. Web API Pods / Containers
Dedicated solely to serving user traffic with zero background task overhead:
```env
# .env on Web Containers
ENABLE_SCHEDULER=false
```
Command:
```bash
gunicorn main:app -w 8 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8020
```

#### 2. Background Scheduler Pod / Container
Dedicated solely to executing scheduled tasks and cron jobs:
```bash
python scripts/run_scheduler.py
```

Systemd service example:
```ini
[Unit]
Description=TashiHome Background Scheduler Daemon
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=tashihome
WorkingDirectory=/var/www/tashihome-backend
ExecStart=/var/www/tashihome-backend/.venv/bin/python scripts/run_scheduler.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## Scheduled Tasks & Maintenance CLI

The application includes a unified CLI tool in `scripts/run_job.py` to inspect and execute scheduled jobs on demand:

```bash
# List all registered scheduled jobs
python scripts/run_job.py --list

# Run a specific job immediately (e.g. refresh public statistics)
python scripts/run_job.py update_public_stats

# Run all registered jobs sequentially
python scripts/run_job.py --all
```

---

## Running Automated Tests

Run the test suite using `pytest`:
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific domain test suites
pytest tests/test_assistant_and_mcp.py -v
pytest tests/test_idempotency.py -v
pytest tests/test_rate_limiter.py -v
pytest tests/test_admin_payout_use_cases.py -v
pytest tests/test_settings_use_cases.py -v
```

---

## Project Documentation Catalog

- [structure.md](structure.md) — Comprehensive codebase architecture, package map, and request flows
- [database.md](database.md) — Complete 36-table database schema, ERD diagrams, and enums reference
- [security.md](security.md) — Authentication, idempotency defenses, rate limiting, SSRF, and Razorpay security
- [phases.md](phases.md) — Implementation roadmap, completed deliverables, and scaling milestones
- [docs/frontend_admin_dashboard_guide.md](docs/frontend_admin_dashboard_guide.md) — Admin dashboard analytics, KPIs, and operational oversight
- [docs/frontend_supply_dashboard_guide.md](docs/frontend_supply_dashboard_guide.md) — Homestay inventory supply dashboard and vendor operations
- [docs/frontend_tax_and_settings_guide.md](docs/frontend_tax_and_settings_guide.md) — Dynamic platform settings, branding assets, and GST calculation guide
- [docs/frontend_ai_assistant_and_mcp_guide.md](docs/frontend_ai_assistant_and_mcp_guide.md) — Frontend integration guide for AI Concierge, SSE streaming, and MCP
- [docs/idempotency_frontend_guide.md](docs/idempotency_frontend_guide.md) — Frontend guide for safe retries and idempotency headers
- [docs/production_notification_guide.md](docs/production_notification_guide.md) — Socket.IO real-time notifications integration guide
- [docs/frontend_notification_angular_guide.md](docs/frontend_notification_angular_guide.md) — Angular real-time notifications client integration
- [docs/frontend_payout_management_guide.md](docs/frontend_payout_management_guide.md) — Host bank account & RazorpayX payout management guide
- [docs/frontend_public_properties_guide.md](docs/frontend_public_properties_guide.md) — Public properties listing, filters, pricing, and sorting
- [docs/frontend_room_block_guide.md](docs/frontend_room_block_guide.md) — Room block and calendar blackout integration guide
- [docs/frontend_room_block_dashboard_guide.md](docs/frontend_room_block_dashboard_guide.md) — Room block management dashboard UI guide
- [docs/frontend_variable_pricing_guide.md](docs/frontend_variable_pricing_guide.md) — Variable occupancy pricing tiers integration guide
- [docs/FRONTEND_API_GUIDE_REVIEWS_TESTIMONIALS.md](docs/FRONTEND_API_GUIDE_REVIEWS_TESTIMONIALS.md) — Reviews and testimonials integration guide


