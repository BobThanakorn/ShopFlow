"""Application settings loaded from environment variables (and .env.local for local dev)."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from zoneinfo import available_timezones

from pydantic import AnyHttpUrl, TypeAdapter, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Anchored to the repo root so `uvicorn` finds it from any working directory.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env.local"

_HTTP_URL = TypeAdapter(AnyHttpUrl)


class Settings(BaseSettings):
    """Runtime configuration.

    Fields are added phase by phase as features need them. Unknown variables are
    ignored, so .env.local can hold the full .env.example from day one.
    """

    model_config = SettingsConfigDict(
        # REVIEW: .env.local is gitignored and deploys go through git, so Vercel never
        # sees it and uses real env vars instead. Do not deploy from a local folder.
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        # REVIEW: a misspelled name (e.g. ADMIN_EMAIL) is silently dropped and the field
        # keeps its default. For admin_emails that means nobody can log in, which fails
        # closed, but check the spelling of every variable set on Vercel.
        extra="ignore",
    )

    # REVIEW: defaults to "production" so a missing APP_ENV fails safe
    # (no static mount, no API docs). Local dev sets "development" in .env.local.
    app_env: Literal["development", "production"] = "production"
    app_base_url: str = "http://localhost:3000"
    admin_emails: Annotated[list[str], NoDecode] = []
    shop_timezone: str = "Asia/Bangkok"

    @field_validator("app_base_url")
    @classmethod
    def _validate_base_url(cls, value: str) -> str:
        # REVIEW: only checks http(s) + host; paths, query strings and userinfo still pass.
        _HTTP_URL.validate_python(value)
        # Stored without a trailing slash so f"{base}/api/..." never yields "//".
        return value.rstrip("/")

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

    @field_validator("shop_timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        value = value.strip()
        # REVIEW: ZoneInfo(value) alone is OS-dependent: Windows' case-insensitive filesystem
        # loads "utc", which then crashes on Vercel's Linux. An exact match against the
        # IANA key list behaves the same everywhere (needs tzdata on Windows/slim Linux).
        if value not in available_timezones():
            raise ValueError(f"unknown IANA timezone: {value!r}")
        return value

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


# REVIEW: cached for the process lifetime, so env changes after the first call are
# invisible. Tests must call get_settings.cache_clear() (see tests/conftest.py).
@lru_cache
def get_settings() -> Settings:
    return Settings()
