# TashiHome Backend

TashiHome Backend is a high-performance, enterprise-grade FastAPI application powering the TashiHome homestay platform. It provides authentication, property & room management, booking workflows, payments, reviews, pre-aggregated analytics, and a multi-worker safe scheduled tasks framework.

---

## Architecture Highlights

- **Layered Architecture**: Strict separation of concerns — API Routes $\to$ Use Cases $\to$ Domain Services $\to$ Repositories $\to$ Models.
- **Pre-Aggregated Public Stats**: Dedicated `public_stats` table updated asynchronously by background jobs to serve homepage statistics in $O(1)$ time with zero multi-table joins.
- **Enterprise Scheduled Jobs (APScheduler)**: Extensible jobs framework with distributed locking via Redis to prevent concurrent execution overlaps.
- **Multi-Worker Safety (Redis Leader Election)**: Only the single elected leader worker runs background scheduler and event subscriber tasks. Standby workers serve HTTP traffic with zero task overhead.
- **Decoupled Production Deployments**: Supports running scheduled tasks embedded in the web leader OR as a dedicated isolated worker process.

---

## Tech Stack

- **Runtime**: Python 3.14+
- **Web Framework**: FastAPI & Uvicorn
- **Database**: PostgreSQL with SQLAlchemy 2.0 (`asyncpg` async driver, `psycopg2` sync driver for Alembic)
- **Cache & Message Broker**: Redis
- **Task Scheduler**: APScheduler (`AsyncIOScheduler`)
- **Database Migrations**: Alembic
- **Settings**: Pydantic Settings (`.env`)

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

Create your local `.env` file from the example:
```bash
cp .env.example .env
```

Ensure the key settings in `.env` match your local environment:
```env
APP_NAME=TashiHome
ENV=development
DEBUG=true
PORT=8020

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tashihome
REDIS_HOST=localhost
REDIS_PORT=6379

ENABLE_SCHEDULER=true
PUBLIC_STATS_UPDATE_INTERVAL_MINUTES=15
```

### 3. Run Database Migrations

Apply all schema migrations up to the latest head:
```bash
alembic upgrade head
```

### 4. Seed Initial Super Admin

Create your initial super admin account:
```bash
python scripts/create_admin.py --email admin@tashihomes.in --password AdminSecurePassword123! --phone +919876543210
```

### 5. Start Application in Development Mode

Run with auto-reload:
```bash
uvicorn main:app --reload --port 8020
```
Or directly:
```bash
python main.py
```

- Swagger UI docs: [http://localhost:8020/docs](http://localhost:8020/docs)
- Health check: [http://localhost:8020/](http://localhost:8020/)
- Public stats: [http://localhost:8020/api/v1/stats](http://localhost:8020/api/v1/stats)

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
> - Workers 2, 3, 4 are standbys $\to$ handle HTTP traffic only.
> - If Worker 1 restarts or crashes, Worker 2 automatically takes over leadership within seconds.

---

### Strategy B: Decoupled Enterprise Deployment (High Traffic / Kubernetes)

For high-traffic or microservices architectures, it is best practice to completely isolate HTTP API servers from background task processing:

#### 1. Web API Pods / Containers
Dedicated solely to serving user traffic with zero CPU/memory interference from background jobs:
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
Or in a systemd service:
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

### Adding New Scheduled Functions

To add a new scheduled function:
1. Create a job class inheriting from `BaseJob` in `app/schedulers/jobs/`:
```python
from app.schedulers.base import BaseJob
from app.schedulers.registry import register_job
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

@register_job
class BookingRemindersJob(BaseJob):
    name = "send_booking_reminders"
    description = "Send check-in reminders to upcoming guests"

    @property
    def trigger(self):
        return CronTrigger(hour=8, minute=0)  # Every day at 8:00 AM

    async def run(self, session: AsyncSession):
        # Business logic with auto session management and Redis distributed locking
        ...
```
2. Import the job class in `app/schedulers/jobs/__init__.py`.

The job will automatically be scheduled, monitored, and available in the CLI runner.

---

## Running Automated Tests

Run the test suite using `pytest`:
```bash
# Run all tests
pytest

# Run scheduled jobs and public stats tests
pytest tests/test_public_stats_scheduler.py -v
```

---

## Project Documentation

- [structure.md](structure.md) — Detailed codebase architecture and request flow
- [database.md](database.md) — Comprehensive database schema, table catalogs, and enum references
- [security.md](security.md) — Authentication, rate limiting, and security policies
- [phases.md](phases.md) — Implementation roadmap and milestones
