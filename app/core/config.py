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



    # JWT configuration
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    # Token expiration times in minutes and days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1 # Minutes until the access token expires
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Days until the refresh token expires
    # Email verification and password reset token expiration times
    EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 24 # Hours until the email verification token expires
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 30 # Minutes until the reset password token expires

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

    @property
    def allowed_hosts(self) -> List[str]:
        if not self.ALLOWED_HOSTS:
            return []
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
