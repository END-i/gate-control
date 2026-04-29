from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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
    admin_username: str = Field(alias="ADMIN_USERNAME")
    admin_password: str = Field(alias="ADMIN_PASSWORD")


@lru_cache
def get_settings() -> Settings:
    return Settings()
