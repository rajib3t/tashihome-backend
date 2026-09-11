# Security Guide & Cybersecurity Assessment

This document outlines the security architecture, defensive input validation strategy, threat modeling, and cybersecurity mitigation controls for the **TashiHome Backend** platform.

---

## 1. Security Architecture & Threat Model

```
+-----------------------------------------------------------------------------------+
|                                Client Applications                                |
|                        (Web Frontend, Mobile App, Vendors)                        |
+-----------------------------------------+-----------------------------------------+
                                          |
                        HTTPS (TLS 1.3)   | + WSS / Socket.IO (JWT Auth Handshake)
                                          v
+-----------------------------------------------------------------------------------+
|                                 API Gateway / WAF                                 |
|               - Rate Limiting (Redis)         - CORS Whitelisting                 |
|               - IP Reputation                 - DDoS / Bot Protection             |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                             FastAPI Application Layer                             |
|  +---------------------------+  +------------------------+  +-------------------+  |
|  |   Idempotency Middleware  |  |  Rate Limiting (Redis) |  |   CSRF Middleware |  |
|  |  (In-Flight Locking / TTL)|  |  (Method Sliding Window|  | (Double-Submit Val|  |
|  +---------------------------+  +------------------------+  +-------------------+  |
|  |      JWT / RBAC Auth      |  |  Socket.IO Room Gating |  | Pydantic Schemas  |  |
|  | (Access/Refresh Tokens)   |  | (Role-Based Isolation) |  | (Strict Validation|  |
|  +---------------------------+  +------------------------+  +-------------------+  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        Application & Domain Use Cases                             |
|  +---------------------------+  +------------------------+  +-------------------+  |
|  |  Business Rules & State   |  | Media Sanitization     |  | Safe Outbound     |  |
|  |  Validation (Ownership)   |  | (EXIF Stripping, WebP) |  | HTTP Client (SSRF)|  |
|  +---------------------------+  +------------------------+  +-------------------+  |
|  |  MCP Tool Parameter Gate  |  | Razorpay Signature HMAC|  | Distributed Locks |  |
|  |  (UUID Opaque Enforce)    |  | (Webhook Verification) |  | (Redis Cron/Leads)|  |
|  +---------------------------+  +------------------------+  +-------------------+  |
+-----------------------------------------+-----------------------------------------+
       |                                  |                                  |
       v                                  v                                  v
+---------------+                +-----------------+                +----------------+
|  PostgreSQL   |                |  Redis Cluster  |                | S3 / CDN Cloud |
| (ORM, Param,  |                | (Token Blacklist|                | (Signed Cookies|
|  Strict Enums)|                |  Idempotency,   |                |  Private ACLs, |
|               |                |  Rate Limiting) |                |  Vector Store) |
+---------------+                +-----------------+                +----------------+
```

---

## 2. Authentication & Access Control

### 2.1 JWT Lifecycle & Token Management
- **Dual-Token Architecture**:
  - **Access Tokens**: Short-lived (e.g., 15–30 minutes) carrying claims (`sub`, `role`, `public_id`, `exp`, `iat`).
  - **Refresh Tokens**: Longer-lived (e.g., 7–30 days) stored in the database (`tokens` table) with revocation flags.
  - **Single-Purpose Tokens**: Specialized token types (`password_reset_token`, `account_activation_token`, `email_verification_token`) strictly validated against their expected `TokenType` enum.
- **Immediate Revocation (Blacklisting)**:
  - On user logout or password change, active tokens are recorded in Redis with a TTL matching the token's remaining lifetime.
  - Incoming requests verify that the token is not present in the Redis blacklist.

### 2.2 Password Security
- **Hashing**: Passwords are hashed using modern, memory-hard algorithms via `pwdlib` (`Argon2id` / `bcrypt` with high work factors).
- **Zero-Plaintext Policy**: Raw passwords are never persisted, cached, emitted in logs, or returned in API response models.
- **Timing-Attack Resistance**: Authentication routines utilize constant-time comparison methods (`hmac.compare_digest`) for secret and token checks.

### 2.3 Role-Based Access Control (RBAC)
- Strict authorization barriers segment endpoints:
  - `/api/v1/admin/*` -> Requires `UserRole.ADMIN`.
  - `/api/v1/vendor/*` -> Requires `UserRole.VENDOR` or `UserRole.ADMIN` with resource-ownership verification.
  - `/api/v1/user/*` / `/api/v1/profile/*` -> Requires authenticated user.
  - `/api/v1/public/*` -> Unauthenticated public read-only access with rate limiting.
- RBAC is enforced declaratively via FastAPI dependency injection (`app.deps`).

### 2.4 CSRF Protection
- State-modifying requests (POST, PUT, PATCH, DELETE) in browser-facing sessions enforce the **Double-Submit Cookie Pattern**:
  - Non-sensitive cookie: `csrf_token` (readable by frontend client).
  - Header validation: `X-CSRF-Token` sent by client and compared via `hmac.compare_digest`.
  - Cookies set with `SameSite=Lax` or `Strict`, `Secure=True`, and proper `Domain` scoping.

### 2.5 Real-Time WebSocket & Socket.IO Security
- **Handshake Authentication**:
  - Socket.IO clients authenticate during the connection handshake via bearer JWT tokens sent in `auth: { token: "..." }` or the `Authorization` header.
  - Expired or revoked tokens are rejected immediately before WebSocket upgrade.
- **Room Isolation & Channel Authorization**:
  - Users are automatically joined only to their authorized private room: `user_{user_id}`.
  - Vendors join `vendor_{vendor_id}` only after role verification.
  - Administrators join `admin_notifications` only if their authenticated role is `admin`.
  - Broadcast notifications are never sent globally without room-level scoping.
- **Cross-Site WebSocket Hijacking (CSWSH) Defense**:
  - Origin verification ensures only authorized frontend domains (`CORS_ALLOWED_ORIGINS`) can initiate WebSocket handshakes.

---

## 3. Defensive Input Validation Approach

TashiHome follows a **Defense-in-Depth Validation Strategy** across three isolated layers:

```
[ Incoming Request ]
        |
        v
+-------------------------------------------------------------+
| Layer 1: Schema & Transport Validation (Pydantic / FastAPI)  |
| - Whitelist allowed payload fields (no extra unexpected keys)|
| - Type checking, length bounds, regex formatting            |
| - URL format validation, UUID structure validation          |
+-------------------------------------------------------------+
        |
        v
+-------------------------------------------------------------+
| Layer 2: Application & Domain Validation (Use Cases)         |
| - Resource ownership verification (vendor owns property)    |
| - State transition validation (draft -> active -> archived) |
| - Business constraint logic (e.g. check-in < check-out)     |
| - Media payload decoding, magic byte check, EXIF stripping  |
+-------------------------------------------------------------+
        |
        v
+-------------------------------------------------------------+
| Layer 3: Persistence & Database Integrity (PostgreSQL)       |
| - Parameterized queries via SQLAlchemy (SQLi prevention)    |
| - Foreign key constraints with explicit ON DELETE actions   |
| - Composite UNIQUE constraints preventing duplicate records |
| - Native PostgreSQL Enum type enforcement                   |
+-------------------------------------------------------------+
```

### 3.1 Media & File Upload Validation
- **MIME Type & Magic Byte Verification**:
  - Base64 / Data URL inputs are parsed using regex (`DATA_URL_PATTERN`) and decoded.
  - MIME types are validated against an allowed whitelist (`image/jpeg`, `image/png`, `image/webp`, `application/pdf`).
- **Image Sanitization & EXIF Stripping**:
  - Uploaded images are re-encoded through Pillow (`PIL.Image`).
  - Privacy-sensitive metadata (GPS coordinates, camera serials, timestamps) is stripped by default unless explicitly extracted.
  - Images are converted to optimized WebP format with dimension caps (e.g., max 1920px) to prevent image decompression bombs (Pixel Floods / Decompression DoS).
- **Direct S3 / Presigned URL Flow**:
  - Direct binary streaming avoids storing untrusted files on local backend disk storage.

### 3.2 AI Concierge & Model Context Protocol (MCP) Security
- **Zero Internal ID Exposure (Opaque UUID Boundary)**:
  - All entities manipulated by the AI Concierge and exposed through MCP tools exclusively utilize `public_id` (UUIDv4) represented as `"id"`.
  - Database primary keys (`BigInteger`) are strictly prohibited from tool arguments, schemas, and return payloads, mitigating horizontal enumeration vulnerabilities.
- **Strict Parameter Whitelisting & Schema Enforcement**:
  - All MCP tool invocations validate incoming arguments using Pydantic schemas with type assertions, regex date bounds (`YYYY-MM-DD`), and range clamps (`guests >= 1`).
- **Read / Write Action Isolation**:
  - Information discovery tools (`search_homestays`, `check_availability`, `get_property_policies`) operate strictly as read-only idempotent queries.
  - Transactional tools (e.g. `create_booking_reservation`, `checkout`) enforce strict customer credential validations, verify room inventory dynamically, and require explicit guest confirmation.
- **Prompt Injection Defense & Guardrails**:
  - System instructions enforce strict role boundaries preventing instruction override from untrusted guest messages.
  - LLM outputs are treated as untrusted strings, requiring escaping and structured JSON parsing before frontend consumption.

---

## 4. Cybersecurity Assessment: Server-Side Request Forgery (SSRF)

Server-Side Request Forgery occurs when an attacker induces the backend server to make HTTP/network requests to an arbitrary, unintended destination (such as internal services, loopback interfaces, or cloud metadata endpoints).

### 4.1 Threat Surface in TashiHome
In this application, outbound network operations occur in:
1. **IP Geolocation Lookup** (`IpService` calling external IP details API).
2. **Media / Asset Processing** (fetching remote assets or downloading webhooks).
3. **Cloud Storage & S3 Endpoints** (connecting to MinIO / AWS S3 APIs).
4. **Third-Party Integrations** (Payment Gateway webhooks, transactional email APIs).

### 4.2 Attack Vectors & Impact
- **Cloud Metadata Compromise**: Accessing `http://169.254.169.254/latest/meta-data/` (AWS/GCP/OpenStack) to extract temporary IAM credentials or instance tokens.
- **Internal Network Scanning & Pivoting**: Probing `http://localhost`, `http://127.0.0.1`, `http://redis:6379`, `http://postgres:5432`, or internal VPC subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
- **DNS Rebinding Attacks**: Resolving a benign domain during validation that switches to a private IP upon request execution.

---

### 4.3 SSRF Mitigation Controls & Secure Implementation

#### Control 1: Strict Endpoint Whitelisting
- Never allow user input to specify arbitrary full URLs for backend fetching.
- Outbound endpoints must be predefined in environment configurations (e.g. `IP_DETAILS_API_URL`).
- Dynamic path segments (such as IP addresses) must be strictly validated before appending:

```python
import ipaddress
from app.core.exceptions import AppException

def validate_public_ip(ip_str: str) -> str:
    """Ensure the provided string is a valid, globally reachable public IP address."""
    try:
        ip = ipaddress.ip_address(ip_str.strip())
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            raise AppException(
                status_code=400,
                message="Invalid IP address provided",
                error_code="INVALID_IP_ADDRESS"
            )
        return str(ip)
    except ValueError:
        raise AppException(
            status_code=400,
            message="Invalid IP format",
            error_code="INVALID_IP_FORMAT"
        )
```

#### Control 2: Safe Outbound HTTP Transport (Anti-SSRF Resolver)
For any service making external HTTP calls (using `httpx` or `aiohttp`):
- **Disable Automatic Redirects** (`follow_redirects=False`) or inspect redirect locations before following.
- **Enforce Allowed Schemes**: Restrict exclusively to `https://`.
- **IP Blacklisting at Socket Level**: Validate resolved IP addresses against private CIDR ranges prior to establishing the TCP connection:

```
Prohibited IP Ranges for Outbound Requests:
- 127.0.0.0/8        (IPv4 Loopback)
- 10.0.0.0/8         (Private Class A)
- 172.16.0.0/12      (Private Class B)
- 192.168.0.0/16     (Private Class C)
- 169.254.0.0/16     (Link-Local / AWS IMDS)
- 0.0.0.0/8          (Broadcast / Current Network)
- ::1/128            (IPv6 Loopback)
- fc00::/7           (IPv6 Unique Local)
- fe80::/10          (IPv6 Link-Local)
```

#### Control 3: Cloud Infrastructure Defenses (IMDSv2)
- **AWS IMDSv2 Mandatory**: Require session-oriented tokens with a hop limit of `1` (`HttpPutResponseHopLimit=1`) to block SSRF requests forwarded through web application proxies.
- **Egress Network Segmentation**: Configure VPC Security Groups and firewall rules so that backend application pods cannot connect directly to internal administrative ports or non-whitelisted external IP ranges.

---

## 5. Additional Cybersecurity Controls

### 5.1 SQL Injection (SQLi) Prevention
- All database interactions use SQLAlchemy 2.0 ORM and `select()` expressions.
- Raw string interpolation into SQL queries is strictly prohibited.
- Dynamic sorting and column filtering are mapped against explicit schema field whitelists.

### 5.2 Cross-Site Scripting (XSS) & Content Security
- API responses enforce `Content-Type: application/json; charset=utf-8`.
- User-supplied rich text or descriptions are sanitized and rendered as escaped text or filtered via strict HTML sanitizers.
- HTTP Security Headers enabled across reverse proxies:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
  - `Content-Security-Policy: default-src 'self'`

### 5.3 Secrets Management & Environment Isolation
- No credentials, tokens, or private keys in git repository.
- Local secrets managed via `.env` (gitignored).
- Production secrets injected via Kubernetes Secrets, AWS Secrets Manager, or HashiCorp Vault.
- `.env.example` provides template keys with dummy values.

### 5.4 Audit & Incident Response
- Comprehensive audit records stored in `login_logs` for anomaly detection.
- Centralized error tracking via Sentry with PII scrubbing (passwords, tokens, cookies redacted).
- Security vulnerability reports should be directed to the security operations team.

---

## 6. Idempotency Engine & Concurrency Attack Defenses (`app/core/idempotency.py`)

To prevent **double-spend attacks**, **race-condition overbooking**, and **accidental duplicate payment requests**, TashiHome enforces an enterprise-grade, Redis-backed idempotency layer.

### 6.1 Idempotency Key Specification
- **Client Header**: Clients supply a unique identifier via `Idempotency-Key` or `X-Idempotency-Key` (UUIDv4 or client transaction identifier, max 255 characters).
- **Scope & Method Applicability**: Applied automatically to state-modifying HTTP methods (`POST`, `PUT`, `PATCH`, `DELETE`). Safe methods (`GET`, `HEAD`, `OPTIONS`) bypass idempotency caching.

### 6.2 In-Flight Execution Locking (Race Condition Prevention)
```
[ Incoming Request with Idempotency-Key ]
                   |
                   v
       +-----------------------+
       | Redis Lock Check      |
       | `idempotency:lock:*`  |
       +-----------+-----------+
                   |
         +---------+---------+
         |                   |
    Lock Acquired       Lock Active
         |                   |
         v                   v
+------------------+  +---------------------------------------------+
| Execute Request  |  | Return HTTP 409 Conflict                    |
| Under 30s Lock   |  | "A request with this key is being processed"|
+------------------+  +---------------------------------------------+
         |
         v
+------------------------------------------+
| Cache Status, Headers & Response Body    |
| (24-Hour TTL in Redis)                   |
+------------------------------------------+
```
- **Distributed In-Flight Lock**: Before executing the route handler, an atomic Redis `SET NX` lock is acquired with a 30-second TTL (`IDEMPOTENCY_LOCK_TIMEOUT_SECONDS`).
- **Concurrent Request Defense**: If a concurrent duplicate request arrives while the first is still processing, the middleware immediately returns **`HTTP 409 Conflict`** with error code `IDEMPOTENT_LOCK_FAILED`, preventing duplicate DB mutations or double charges.

### 6.3 Request Fingerprinting & Cache Verification
- **SHA-256 Fingerprint**: To prevent key-tampering (e.g. an attacker reusing another user's key with different payload), each key is hashed alongside the request signature:
  $$\text{Fingerprint} = \text{SHA-256}(\text{Method} \parallel \text{Path} \parallel \text{User ID / IP} \parallel \text{Raw Body})$$
- **Replay Response**: Subsequent requests with identical idempotency keys return the cached response immediately from Redis with:
  - Header: `Idempotent-Replay: true`
  - Original HTTP status code and response payload.
  - Response cache duration: 24 hours (`IDEMPOTENCY_EXPIRE_SECONDS = 86400`).

---

## 7. Enterprise Rate Limiting & Cooldown Protection (`app/core/rate_limiter.py`)

TashiHome implements a multi-tier sliding-window rate limiter powered by Redis to safeguard API endpoints against denial-of-service (DoS), brute-force password guessing, and automated scraping.

### 7.1 Method-Specific Quotas
Configured centrally via `app/core/config.py`:
- **GET**: 120 requests / 60 seconds (`RATE_LIMIT_GET_MAX_REQUESTS`)
- **POST**: 30 requests / 60 seconds (`RATE_LIMIT_POST_MAX_REQUESTS`)
- **PUT**: 30 requests / 60 seconds (`RATE_LIMIT_PUT_MAX_REQUESTS`)
- **PATCH**: 30 requests / 60 seconds (`RATE_LIMIT_PATCH_MAX_REQUESTS`)
- **DELETE**: 20 requests / 60 seconds (`RATE_LIMIT_DELETE_MAX_REQUESTS`)
- **Default Fallback**: 60 requests / 60 seconds

### 7.2 Abusive Client Cooldown Lockout
- **Automatic Cooldown Trigger**: When a client breaches their rate limit quota, an extended lockout penalty is initiated (`RATE_LIMIT_COOLDOWN_SECONDS`, default: **3600 seconds / 1 hour**).
- **Hard Block During Cooldown**: While in cooldown, all subsequent requests are rejected immediately at the gateway layer without consuming application or database resources.
- **RFC Standard Compliance Headers**:
  - `X-RateLimit-Limit`: Maximum allowed requests per window.
  - `X-RateLimit-Remaining`: Remaining quota in current window.
  - `X-RateLimit-Reset`: Unix timestamp when current window expires.
  - `Retry-After`: Seconds until cooldown penalty expires (on HTTP 429).

---

## 8. Payment Gateway & Webhook Security (Razorpay & RazorpayX)

### 8.1 Cryptographic Webhook Signature Verification
- Inbound webhooks from Razorpay (e.g. `payment.captured`, `refund.processed`, `payout.processed`) are strictly authenticated:
  - Raw request payload bytes are hashed with HMAC SHA-256 using the pre-shared secret `RAZORPAY_WEBHOOK_SECRET`.
  - The computed signature is compared against the `X-Razorpay-Signature` header using `hmac.compare_digest` to prevent timing attacks.
  - Unsigned or mismatched webhooks are rejected with `HTTP 400 Bad Request` and logged.

### 8.2 Host Bank Account & Payout Safeguards
- **Beneficiary Verification**: Vendor bank accounts (`vendor_bank_accounts`) must undergo administrative verification (`is_verified=True`) before fund disbursement can be triggered.
- **Admin-Only Payout Initiation**: Payout operations (`/api/v1/admin/payouts/*`) are restricted strictly to administrators with `UserRole.ADMIN`.
- **Financial Audit Immutability**: All payment, payout, and refund records use foreign keys with `ON DELETE RESTRICT` constraints, ensuring immutable transaction history.

---

## 9. Content Delivery & Media Storage Security (CloudFront & S3)

### 9.1 S3 Bucket Isolation
- S3 object storage buckets (`tashihome-assets`, `tashihome-vector`) are private with public access blocks enabled.
- Access is restricted exclusively to application IAM service roles and signed CloudFront distributions.

### 9.2 CloudFront Signed Cookies & URL Protection
- Premium or private media assets are distributed through Amazon CloudFront using **RSA Private Key Signed Cookies**:
  - `CloudFront-Policy`
  - `CloudFront-Signature`
  - `CloudFront-Key-Pair-Id`
- Cookies are scoped to the apex domain (`.tashihomes.in`) with short TTLs (`CLOUDFRONT_COOKIE_TTL = 3600s`), preventing unauthorized media hotlinking.
