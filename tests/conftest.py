from collections.abc import Iterator
from pathlib import Path

import pytest

from app.config import Settings, get_settings

REPO_ROOT = Path(__file__).resolve().parent.parent
# Captured before isolated_env patches it, so a test can still check the real value.
CONFIGURED_ENV_FILE = Settings.model_config["env_file"]


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Keep the developer's shell env and .env.local out of every test."""
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    # Tests that exercise env-file loading pass `_env_file=` explicitly.
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
