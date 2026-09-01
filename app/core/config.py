from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, List
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str
    # Database URL 
    DATABASE_URL: str
    # Redis configuration
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # Rate Limiting configuration (setting-driven)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_COOLDOWN_SECONDS: int = 3600     # Cooldown duration in seconds when rate limit is exceeded (default: 1 hour = 3600s)
    RATE_LIMIT_KEY_PREFIX: str = "ratelimit"    # Redis key prefix for rate limiting

    # HTTP method-specific rate limits (requests per window)
    RATE_LIMIT_GET_MAX_REQUESTS: int = 120
    RATE_LIMIT_GET_WINDOW_SECONDS: int = 60

    RATE_LIMIT_POST_MAX_REQUESTS: int = 30
    RATE_LIMIT_POST_WINDOW_SECONDS: int = 60

    RATE_LIMIT_PUT_MAX_REQUESTS: int = 30
    RATE_LIMIT_PUT_WINDOW_SECONDS: int = 60

    RATE_LIMIT_PATCH_MAX_REQUESTS: int = 30
    RATE_LIMIT_PATCH_WINDOW_SECONDS: int = 60

    RATE_LIMIT_DELETE_MAX_REQUESTS: int = 20
    RATE_LIMIT_DELETE_WINDOW_SECONDS: int = 60

    # Default fallback for other HTTP methods
    RATE_LIMIT_DEFAULT_MAX_REQUESTS: int = 60
    RATE_LIMIT_DEFAULT_WINDOW_SECONDS: int = 60

    def get_rate_limit_for_method(self, method: str) -> tuple[int, int]:
        """Return (max_requests, window_seconds) for a given HTTP method."""
        m = (method or "").upper()
        if m == "GET":
            return self.RATE_LIMIT_GET_MAX_REQUESTS, self.RATE_LIMIT_GET_WINDOW_SECONDS
        elif m == "POST":
            return self.RATE_LIMIT_POST_MAX_REQUESTS, self.RATE_LIMIT_POST_WINDOW_SECONDS
        elif m == "PUT":
            return self.RATE_LIMIT_PUT_MAX_REQUESTS, self.RATE_LIMIT_PUT_WINDOW_SECONDS
        elif m == "PATCH":
            return self.RATE_LIMIT_PATCH_MAX_REQUESTS, self.RATE_LIMIT_PATCH_WINDOW_SECONDS
        elif m == "DELETE":
            return self.RATE_LIMIT_DELETE_MAX_REQUESTS, self.RATE_LIMIT_DELETE_WINDOW_SECONDS
        return self.RATE_LIMIT_DEFAULT_MAX_REQUESTS, self.RATE_LIMIT_DEFAULT_WINDOW_SECONDS

    # Idempotency Configuration (Redis-backed)
    IDEMPOTENCY_ENABLED: bool = True
    IDEMPOTENCY_EXPIRE_SECONDS: int = 86400        # Response cache duration: 24 hours (86400s)
    IDEMPOTENCY_LOCK_TIMEOUT_SECONDS: int = 30     # In-flight lock timeout in seconds
    IDEMPOTENCY_KEY_PREFIX: str = "idempotency"    # Redis key prefix
    # JWT configuration
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    # Token expiration times in minutes and days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1 # Minutes until the access token expires
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Days until the refresh token expires
    # Email verification and password reset token expiration times
    EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 24 # Hours until the email verification token expires
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 30 # Minutes until the reset password token expires

    # Account activation 
    ACCOUNT_ACTIVATION_HOURS : int = 24 #  Hours until the Account activation token expires
    #  Frontend URL for sending email verification and password reset links
    FRONTEND_URL: str = "http://localhost:4200"

    # CORS configuration
    CORS_ALLOWED_ORIGINS: Optional[str] = None

    @property
    def cors_allowed_origins(self) -> List[str]:
        if not self.CORS_ALLOWED_ORIGINS:
            return ["http://localhost:3000", "http://localhost:5173"]
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def cookie_samesite(self) -> str:
        value = (self.COOKIE_SAMESITE or "").strip().lower()
        if not value:
            return "none" if self.SECURE_COOKIES else "lax"
        if value in {"lax", "strict", "none"}:
            return value
        return "lax"
    COOKIE_DOMAIN: Optional[str] = None  # Domain for setting cookies, e.g., ".example.com"
    # Environment
    ENV: str = "development"  # production | staging | development
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECURE_COOKIES: bool = False
    COOKIE_SAMESITE: Optional[str] = None
    PORT: int = 8020

    # S3 configuration 
    S3_PROVIDER: Optional[str] = None  # 'aws' or 'minio' (optional)
    S3_ENDPOINT_URL: Optional[str] = None
    S3_REGION: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_USE_SSL: bool = True


    # Login Log Settings
    LOGIN_LOG_ENABLED: bool = True
    IP_DETAILS_API_URL: Optional[str] = None

    # Allowed hosts for TrustedHostMiddleware
    ALLOWED_HOSTS: Optional[str] = None
     # Email Settings (Multiple Providers Supported)
    EMAIL_PROVIDER: str = "mock" # options: "mock", "smtp", "mailgun", "brevo"
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Mailgun
    MAILGUN_DOMAIN: Optional[str] = None
    MAILGUN_API_KEY: Optional[str] = None
    
    # Brevo
    BREVO_API_KEY: Optional[str] = None

    CLOUDFRONT_DOMAIN: Optional[str] = None
    CLOUDFRONT_KEY_PAIR_ID: Optional[str] = None
    CLOUDFRONT_PRIVATE_KEY_PATH: Optional[str] = None
    CLOUDFRONT_COOKIE_DOMAIN: Optional[str]  = ".tashihomes.in"
    CLOUDFRONT_COOKIE_TTL: Optional[int]  = 3600

    # Razorpay / Payment Configuration
    PAYMENT_ENABLED: bool = True
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    RAZORPAYX_ACCOUNT_NUMBER: Optional[str] = None
    DEFAULT_COMMISSION_PERCENTAGE: float = 10.0


    @property
    def allowed_hosts(self) -> List[str]:
        if not self.ALLOWED_HOSTS:
            return []
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
