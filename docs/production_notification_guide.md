# Production Deployment Guide: Real-Time & Persistent Notifications

This guide covers everything required to deploy, scale, and maintain the **Socket.IO Real-Time & Persistent Notification System** in production across the **FastAPI Backend**, **Redis Cluster**, **Nginx/Load Balancer**, and **Angular Frontend (AWS Amplify / Web)**.

---

## Table of Contents
1. [Production Architecture Overview](#1-production-architecture-overview)
2. [Multi-Worker & Multi-Server Clustering (Redis Pub/Sub)](#2-multi-worker--multi-server-clustering-redis-pubsub)
3. [Nginx Reverse Proxy & Load Balancer Configuration](#3-nginx-reverse-proxy--load-balancer-configuration)
4. [Cloudflare & AWS ALB Configuration](#4-cloudflare--aws-alb-configuration)
5. [Backend Production Environment (`.env`)](#5-backend-production-environment-env)
6. [Frontend Angular Production Configuration](#6-frontend-angular-production-configuration)
7. [SSL / HTTPS / WSS Security](#7-ssl--https--wss-security)
8. [Monitoring, Health Checks & Log Troubleshooting](#8-monitoring-health-checks--log-troubleshooting)
9. [Pre-Flight Production Checklist](#9-pre-flight-production-checklist)

---

## 1. Production Architecture Overview

```
                                  [ Users / Browsers / Mobile ]
                                                │
                                    HTTPS / WSS (Port 443)
                                                ▼
                                    ┌───────────────────────┐
                                    │  Nginx / Cloudflare   │
                                    │  SSL Termination &    │
                                    │  WebSocket Upgrade    │
                                    └───────────┬───────────┘
                                                │
                    ┌───────────────────────────┴───────────────────────────┐
                    │                                                       │
         HTTP REST (/api/v1/...)                                WebSocket Handshake (/socket.io/...)
                    ▼                                                       ▼
    ┌───────────────────────────────┐                       ┌───────────────────────────────┐
    │  FastAPI Backend (Worker 1)   │                       │  FastAPI Backend (Worker 2)   │
    │  - DB CRUD: Notification Model│                       │  - Active Sockets: User/Role  │
    │  - Socket.IO ASGI App         │                       │  - Socket.IO ASGI App         │
    └───────────────┬───────────────┘                       └───────────────┬───────────────┘
                    │                                                       │
                    │                  Redis Pub/Sub Bus                    │
                    └───────────────────────────┬───────────────────────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │     Redis Server      │
                                    │   (AsyncRedisManager) │
                                    └───────────────────────┘
                                                ▲
                                                │ Persistent Storage
                                    ┌───────────┴───────────┐
                                    │  PostgreSQL Database  │
                                    │  `notifications` table│
                                    └───────────────────────┘
```

### Key Components
1. **PostgreSQL**: Stores persistent notification rows (`id`, `user_id`, `role`, `type`, `title`, `message`, `data`, `is_read`, `read_at`).
2. **Redis (`AsyncRedisManager`)**: Distributes Socket.IO emits across all backend processes/containers so clients connected to Worker A receive broadcasts triggered by REST calls processed by Worker B.
3. **Nginx / ALB**: Terminates TLS (`https://` and `wss://`), handles HTTP upgrade headers for WebSockets, and routes traffic to Uvicorn workers.
4. **Angular Frontend**: Automatically connects to the secure socket (`wss://api.tashihomes.in/socket.io/`), syncs real-time state with Angular Signals, and falls back to REST API for notification history.

---

## 2. Multi-Worker & Multi-Server Clustering (Redis Pub/Sub)

In production, Python backends run multiple processes (e.g. Uvicorn with multiple workers or multiple Docker containers). 

When guest creates a booking request, the HTTP POST request lands on **Worker 1**. If host's socket is connected to **Worker 2**, Worker 1 must broadcast the notification through Redis so Worker 2 delivers it to the host.

### Enabling Multi-Worker Redis in Backend

Set the following in your production `.env`:

```env
# Enable Redis Pub/Sub for Socket.IO clustering
SOCKETIO_REDIS_ENABLED=true
REDIS_HOST=127.0.0.1       # Or your managed Redis host (e.g. AWS ElastiCache)
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_redis_password
REDIS_DB=0
```

When `SOCKETIO_REDIS_ENABLED=true`, `app/core/socket.py` automatically initializes `socketio.AsyncRedisManager`.

### Running with Gunicorn + Uvicorn Workers

In production, use **Gunicorn** managing **Uvicorn workers**:

```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8020 \
  --access-logfile - \
  --error-logfile - \
  --timeout 120 \
  --keep-alive 5
```

---

## 3. Nginx Reverse Proxy & Load Balancer Configuration

WebSockets require an explicit HTTP 1.1 `Upgrade` header handshake. The default Nginx configuration drops these headers unless configured.

### Production Nginx Site Configuration (`/etc/nginx/sites-available/tashihome-api`)

```nginx
# Upstream Uvicorn backend cluster
upstream fastapi_backend {
    # If using polling transport fallback across multiple workers, use ip_hash:
    ip_hash;
    server 127.0.0.1:8020;
    keepalive 32;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name api.tashihomes.in;
    return 301 https://$host$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name api.tashihomes.in;

    # SSL Certificates (Let's Encrypt / Certbot)
    ssl_certificate /etc/letsencrypt/live/api.tashihomes.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tashihomes.in/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Max upload body size for image uploads
    client_max_body_size 25M;

    # 1. Socket.IO WebSocket and Polling Endpoints
    location /socket.io/ {
        proxy_pass http://fastapi_backend/socket.io/;
        proxy_http_version 1.1;

        # Crucial: WebSocket Upgrade headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable proxy buffering for real-time streaming
        proxy_buffering off;

        # Long timeouts to prevent Nginx from killing idle WebSocket connections (24 hours)
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_connect_timeout 60s;
    }

    # 2. REST API Endpoints
    location / {
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 120s;
    }
}
```

Verify and reload Nginx:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 4. Cloudflare & AWS ALB Configuration

### Cloudflare
If using Cloudflare in front of your domain:
1. Go to **Network** in Cloudflare Dashboard.
2. Ensure **WebSockets** is toggled **ON**.
3. Under **SSL/TLS**, set mode to **Full (strict)**.
4. If using Cloudflare WAF / Bot Fight Mode, whitelist `/socket.io/*` so websocket upgrade handshakes are not challenged with JS puzzles.

### AWS Application Load Balancer (ALB)
1. **Target Group**: Ensure target group protocol is HTTP (Port 8020).
2. **Idle Timeout**: Increase ALB idle timeout to at least **300 seconds** (default 60 seconds may disconnect quiet sockets).
3. **Stickiness**: If Socket.IO transports allow `polling`, enable **Target Group Stickiness (Cookie-based)** so polling requests from the same handshake reach the same worker. If using WebSocket only (`transports: ['websocket']`), stickiness is not required.

---

## 5. Backend Production Environment (`.env`)

Configure the backend `.env` file on the production server:

```env
# Application
APP_NAME=TashiHome Backend
ENV=production
DEBUG=false
LOG_LEVEL=INFO
PORT=8020

# Database
DATABASE_URL=postgresql+asyncpg://prod_user:prod_password@db-host:5432/tashihome_db

# Redis & Socket.IO Clustering
REDIS_HOST=redis-host-or-ip
REDIS_PORT=6379
REDIS_PASSWORD=strong_redis_password
REDIS_DB=0
SOCKETIO_REDIS_ENABLED=true

# Security & CORS (List production domains explicitly)
FRONTEND_URL=https://tashihomes.in
CORS_ALLOWED_ORIGINS=https://tashihomes.in,https://www.tashihomes.in,https://admin.tashihomes.in
ALLOWED_HOSTS=api.tashihomes.in,localhost

# JWT Configuration
JWT_SECRET=use_a_strong_64_character_random_secret_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Cookie Security
SECURE_COOKIES=true
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=.tashihomes.in
```

---

## 6. Frontend Angular Production Configuration

The frontend (`/tashihome`) uses AWS Amplify or static hosting with environment generation via `scripts/generate-environment.mjs`.

### 1. Build Environment Variables (Amplify / CI/CD)

In AWS Amplify Console > **Environment variables**, set:

| Variable | Recommended Production Value | Description |
|---|---|---|
| `API_URL` | `https://api.tashihomes.in` | Base backend API URL |
| `SOCKET_URL` | `https://api.tashihomes.in` | Socket.IO server URL (WSS) |
| `SOCKET_PATH` | `/socket.io` | Handshake path |
| `APPLICATION_NAME` | `Tashi Home` | Brand title |
| `DISABLE_PAYMENT` | `false` | Enable Razorpay payments |
| `ENABLE_CHATBOX` | `true` | Enable live chat/notification widgets |

When `bun run build` executes, `scripts/generate-environment.mjs` populates `src/environments/environment.prod.ts` with these values automatically.

### 2. Frontend Connection Lifecycle (`NotificationSocketService`)

The frontend features:
- **SSR Safety**: Guards against `window` / `localStorage` access on server side using `isPlatformBrowser(platformId)`.
- **Reactive Auth Sync**: Automatically connects the socket when user logs in (`effect()` on `authService.authUser`), and disconnects on logout.
- **Exponential Reconnection**: Reconnects up to 15 times with 2s to 10s jitter.
- **Auditory Chime**: Zero-dependency Web Audio API harmonic chime for incoming notifications.
- **Optimistic UI**: Marks notifications as read instantly in Angular Signals before awaiting server response.

---

## 7. SSL / HTTPS / WSS Security

In production:
1. **Never use `ws://` on an `https://` site**: Browsers block unencrypted WebSockets on HTTPS pages due to mixed-content security policies.
2. When Angular connects to `https://api.tashihomes.in`, the browser automatically upgrades to `wss://api.tashihomes.in/socket.io/`.
3. Handshake Authentication:
   - Handshake passes JWT token in `auth: { token }` payload and `?token=` query param.
   - Handshake validates active DB user and rejects expired/revoked tokens.
   - Expired tokens receive clean `401 Unauthorized` responses.

---

## 8. Monitoring, Health Checks & Log Troubleshooting

### Useful Backend Log Messages

| Log Message | Meaning | Action Needed |
|---|---|---|
| `Socket.IO initialized with AsyncRedisManager` | Redis cluster adapter is active | Everything normal |
| `Socket connected: sid=..., user=123, role=vendor` | Successful authenticated client connection | Normal |
| `Handshake auth missing token` | Client attempted unauthenticated socket connection | Check client auth service |
| `Handshake user ... is inactive or not found` | Blocked or invalid user tried to connect | Normal security rejection |
| `WebSocket connection to ... failed` (Client console) | Client cannot reach backend port or proxy misconfigured | Check Nginx upgrade headers and backend uptime |

### Testing Real-Time Notifications in Production

1. Open browser console on `https://tashihomes.in`.
2. Inspect the Network tab -> Filter by `WS`:
   - Verify connection to `wss://api.tashihomes.in/socket.io/?...`.
   - Response code must be `101 Switching Protocols`.
3. Create a test booking request:
   - Check Vendor and Admin dashboard bell icons: unread badge counter should increment immediately with audio chime.

---

## 9. Pre-Flight Production Checklist

- [ ] `SOCKETIO_REDIS_ENABLED=true` set in production backend `.env`.
- [ ] Redis server running and accessible from backend instances.
- [ ] `CORS_ALLOWED_ORIGINS` includes the production frontend domains (e.g. `https://tashihomes.in`).
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` is set to reasonable lifetime (e.g. `60` minutes).
- [ ] Nginx includes `proxy_set_header Upgrade $http_upgrade;` and `proxy_set_header Connection "upgrade";` for `/socket.io/`.
- [ ] Nginx `proxy_read_timeout` is set to `86400s` to prevent premature disconnects.
- [ ] Angular Amplify environment variables `API_URL` and `SOCKET_URL` point to `https://api.tashihomes.in`.
- [ ] Cloudflare WebSockets toggle is enabled (if using Cloudflare).
- [ ] Alembic migration `b8c9d0e1f2a3_add_notifications_table` is applied to production PostgreSQL.

