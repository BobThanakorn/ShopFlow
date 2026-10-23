from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import ENV_FILE, Settings, get_settings


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


def test_env_local_path_is_anchored_to_repo_root(
    repo_root: Path, configured_env_file: object
) -> None:
    # A cwd-relative path would silently skip .env.local when uvicorn runs elsewhere.
    assert repo_root / ".env.local" == ENV_FILE
    assert configured_env_file == ENV_FILE


@pytest.fixture
def development_env_file(tmp_path: Path) -> Path:
    env_file = tmp_path / ".env.local"
    env_file.write_text("APP_ENV=development\n", encoding="utf-8")
    return env_file


def test_reads_env_file(development_env_file: Path) -> None:
    assert Settings(_env_file=development_env_file).app_env == "development"


def test_environment_variable_overrides_env_file(
    monkeypatch: pytest.MonkeyPatch, development_env_file: Path
) -> None:
    monkeypatch.setenv("APP_ENV", "production")

    assert Settings(_env_file=development_env_file).app_env == "production"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://localhost:3000", "http://localhost:3000"),
        ("https://shopflow.example.com/", "https://shopflow.example.com"),
    ],
)
def test_base_url_validated_and_trailing_slash_stripped(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: str
) -> None:
    monkeypatch.setenv("APP_BASE_URL", raw)

    assert Settings().app_base_url == expected


@pytest.mark.parametrize("raw", ["localhost:3000", "ftp://example.com", "not a url"])
def test_rejects_invalid_base_url(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    monkeypatch.setenv("APP_BASE_URL", raw)

    with pytest.raises(ValidationError):
        Settings()


def test_accepts_valid_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHOP_TIMEZONE", "Asia/Tokyo")

    assert Settings().shop_timezone == "Asia/Tokyo"


@pytest.mark.parametrize("raw", ["Asia/Bangkokk", "GMT+7", "../etc/passwd"])
def test_rejects_unknown_timezone(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    monkeypatch.setenv("SHOP_TIMEZONE", raw)

    with pytest.raises(ValidationError):
        Settings()


def test_env_example_parses_as_documented(repo_root: Path) -> None:
    # Guards the inline "# comment" style in .env.example: values must not include them.
    settings = Settings(_env_file=repo_root / ".env.example")

    assert settings.app_env == "development"
    assert settings.app_base_url == "http://localhost:3000"
    assert settings.admin_emails == ["owner@example.com"]
    assert settings.shop_timezone == "Asia/Bangkok"


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
