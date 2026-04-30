from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(alias="DATABASE_URL")
    secret_key: str = Field(alias="SECRET_KEY")
    relay_ip: str = Field(alias="RELAY_IP")
    relay_username: str = Field(alias="RELAY_USERNAME")
    relay_password: str = Field(alias="RELAY_PASSWORD")
    frontend_url: str = Field(alias="FRONTEND_URL")
    webhook_shared_secret: str = Field(alias="WEBHOOK_SHARED_SECRET")
    webhook_auth_mode: Literal["token", "hmac"] = Field(default="token", alias="WEBHOOK_AUTH_MODE")
    webhook_hmac_secret: str = Field(default="", alias="WEBHOOK_HMAC_SECRET")
    webhook_max_skew_seconds: int = Field(default=300, alias="WEBHOOK_MAX_SKEW_SECONDS")
    webhook_max_image_bytes: int = Field(default=5_242_880, alias="WEBHOOK_MAX_IMAGE_BYTES")
    app_env: str = Field(default="development", alias="APP_ENV")
    auto_create_schema: str = Field(default="", alias="AUTO_CREATE_SCHEMA")
    auth_login_rate_limit: int = Field(default=20, alias="AUTH_LOGIN_RATE_LIMIT")
    auth_login_rate_window_seconds: int = Field(default=60, alias="AUTH_LOGIN_RATE_WINDOW_SECONDS")
    webhook_rate_limit: int = Field(default=120, alias="WEBHOOK_RATE_LIMIT")
    webhook_rate_window_seconds: int = Field(default=60, alias="WEBHOOK_RATE_WINDOW_SECONDS")
    admin_username: str = Field(alias="ADMIN_USERNAME")
    admin_password: str = Field(alias="ADMIN_PASSWORD")
    admin_role: str = Field(default="admin", alias="ADMIN_ROLE")
    sensitive_rate_limit: int = Field(default=60, alias="SENSITIVE_RATE_LIMIT")
    sensitive_rate_window_seconds: int = Field(default=60, alias="SENSITIVE_RATE_WINDOW_SECONDS")
    relay_worker_poll_seconds: int = Field(default=1, alias="RELAY_WORKER_POLL_SECONDS")
    relay_worker_retry_seconds: int = Field(default=5, alias="RELAY_WORKER_RETRY_SECONDS")
    relay_worker_max_attempts: int = Field(default=3, alias="RELAY_WORKER_MAX_ATTEMPTS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    redis_url: str = Field(default="", alias="REDIS_URL")
    metrics_api_key: str = Field(default="", alias="METRICS_API_KEY")
    trusted_proxy_ips: str = Field(default="", alias="TRUSTED_PROXY_IPS")
    vault_addr: str = Field(default="", alias="VAULT_ADDR")
    vault_token: str = Field(default="", alias="VAULT_TOKEN")
    vault_secret_path: str = Field(default="secret/data/anpr", alias="VAULT_SECRET_PATH")
    # Media storage
    media_storage_backend: Literal["local", "s3"] = Field(default="local", alias="MEDIA_STORAGE_BACKEND")
    media_retention_hot_days: int = Field(default=30, alias="MEDIA_RETENTION_HOT_DAYS")
    s3_bucket: str = Field(default="", alias="S3_BUCKET")
    s3_endpoint_url: str = Field(default="", alias="S3_ENDPOINT_URL")
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    s3_public_base_url: str = Field(default="", alias="S3_PUBLIC_BASE_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
