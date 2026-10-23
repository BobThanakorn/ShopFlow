"""Application settings loaded from environment variables (and .env.local for local dev)."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Fields are added phase by phase as features need them. Unknown variables are
    ignored, so .env.local can hold the full .env.example from day one.
    """

    model_config = SettingsConfigDict(
        # REVIEW: relative to the working directory. Fine for `uvicorn` run from the repo
        # root; on Vercel the file does not exist and real env vars are used instead.
        env_file=".env.local",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # REVIEW: defaults to "production" so a missing APP_ENV fails safe
    # (no static mount, no API docs). Local dev sets "development" in .env.local.
    app_env: Literal["development", "production"] = "production"
    app_base_url: str = "http://localhost:3000"
    admin_emails: Annotated[list[str], NoDecode] = []
    shop_timezone: str = "Asia/Bangkok"

    @field_validator("admin_emails", mode="before")
    @classmethod
    def _split_admin_emails(cls, value: object) -> object:
        # REVIEW: normalised to lowercase here; auth.py (Phase 4) must lowercase the
        # token's email before comparing, or mixed-case logins will be rejected.
        if isinstance(value, str):
            value = value.split(",")
        if isinstance(value, list):
            return [str(email).strip().lower() for email in value if str(email).strip()]
        return value

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
