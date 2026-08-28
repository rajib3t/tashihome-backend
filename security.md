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
                        HTTPS (TLS 1.3)   | + CSRF Token Header / Cookies
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
|  |     CSRF Middleware       |  |   JWT / RBAC Auth      |  | Pydantic Schemas  |  |
|  | (Double-Submit Token Val) |  | (Access/Refresh Tokens)|  | (Type & Boundary) |  |
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
+-----------------------------------------+-----------------------------------------+
       |                                  |                                  |
       v                                  v                                  v
+---------------+                +-----------------+                +----------------+
|  PostgreSQL   |                |  Redis Cluster  |                | S3 / CDN Cloud |
| (ORM, Param,  |                | (Token Blacklist|                | (Presigned URLs|
|  Strict Enums)|                |  Rate Limiting) |                |  Private ACLs) |
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

### 5.4 Rate Limiting & Abuse Prevention
- Redis token-bucket rate limiting applied on sensitive routes:
  - `/api/v1/auth/login` (prevent brute-force password guessing).
  - `/api/v1/auth/forgot-password` (prevent email enumeration & spam).
  - `/api/v1/auth/register` (prevent automated bot registration).

### 5.5 Audit & Incident Response
- Comprehensive audit records stored in `login_logs` for anomaly detection.
- Centralized error tracking via Sentry with PII scrubbing (passwords, tokens, cookies redacted).
- Security vulnerability reports should be directed to the security operations team.
