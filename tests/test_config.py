from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings
from tests.conftest import REPO_ROOT


def test_defaults_fail_safe_to_production() -> None:
    settings = Settings()

    assert settings.app_env == "production"
    assert settings.is_development is False
    assert settings.admin_emails == []
    assert settings.shop_timezone == "Asia/Bangkok"


def test_reads_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APP_BASE_URL", "https://shopflow.example.com")

    settings = Settings()

    assert settings.is_development is True
    assert settings.app_base_url == "https://shopflow.example.com"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("owner@example.com", ["owner@example.com"]),
        (" Owner@Example.com , staff@example.com ", ["owner@example.com", "staff@example.com"]),
        ("a@example.com,,b@example.com,", ["a@example.com", "b@example.com"]),
    ],
)
def test_admin_emails_comma_separated(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]
) -> None:
    monkeypatch.setenv("ADMIN_EMAILS", raw)

    assert Settings().admin_emails == expected


def test_admin_emails_accepts_list_in_code() -> None:
    assert Settings(admin_emails=[" A@Example.com "]).admin_emails == ["a@example.com"]


def test_rejects_unknown_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")

    with pytest.raises(ValidationError):
        Settings()


def test_empty_value_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "")

    assert Settings().app_env == "production"


def test_reads_env_local_from_working_directory(tmp_path: Path) -> None:
    (tmp_path / ".env.local").write_text("APP_ENV=development\n", encoding="utf-8")

    assert Settings().app_env == "development"


def test_environment_variable_overrides_env_local(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".env.local").write_text("APP_ENV=development\n", encoding="utf-8")
    monkeypatch.setenv("APP_ENV", "production")

    assert Settings().app_env == "production"


def test_env_example_parses_as_documented() -> None:
    # Guards the inline "# comment" style in .env.example: values must not include them.
    settings = Settings(_env_file=REPO_ROOT / ".env.example")

    assert settings.app_env == "development"
    assert settings.app_base_url == "http://localhost:3000"
    assert settings.admin_emails == ["owner@example.com"]
    assert settings.shop_timezone == "Asia/Bangkok"


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
