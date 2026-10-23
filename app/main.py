"""FastAPI application. Vercel loads `app.main:app` (see [tool.vercel] in pyproject.toml)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    is_dev = settings.is_development

    app = FastAPI(
        title="ShopFlow",
        # REVIEW: interactive docs only in development to keep the production surface small.
        docs_url="/api/docs" if is_dev else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if is_dev else None,
    )

    @app.get("/api/health")
    # HEAD too: some free uptime monitors probe with HEAD and treat 405 as down. Kept out
    # of the schema so OpenAPI does not get a duplicate operation ID.
    @app.head("/api/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        # Phase 1 adds a database check here.
        return {"status": "ok"}

    if is_dev:
        # REVIEW: must stay after every route — a mount at "/" swallows paths registered
        # later. On Vercel the CDN serves public/ and the docs say not to mount it.
        app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")

    return app


# REVIEW: runs at import time and reads real settings, so importing app.main with a bad
# env or .env.local raises immediately. Tests import it lazily, after isolated_env.
app = create_app()
