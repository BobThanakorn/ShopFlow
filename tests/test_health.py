import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(app_env: str) -> TestClient:
    return TestClient(create_app(Settings(app_env=app_env)))


@pytest.mark.parametrize("app_env", ["production", "development"])
def test_health_returns_ok(app_env: str) -> None:
    # In development the "/" static mount must not shadow API routes.
    response = make_client(app_env).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_public_dir_served_in_development() -> None:
    response = make_client("development").get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_public_dir_not_mounted_in_production() -> None:
    assert make_client("production").get("/").status_code == 404


def test_api_docs_only_in_development() -> None:
    assert make_client("production").get("/api/openapi.json").status_code == 404
    assert make_client("development").get("/api/openapi.json").status_code == 200


def test_vercel_entrypoint_exposes_module_level_app() -> None:
    from app import main

    assert isinstance(main.app, FastAPI)
