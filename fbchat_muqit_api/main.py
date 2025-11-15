"""ASGI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from .config import APISettings
from .routes import create_router
from .service import GroupScraperService

API_DESCRIPTION = (
    "Lightweight HTTP facade for fbchat-muqit. The API accepts payloads that "
    "mirror the Apify Facebook group scraper input schema and returns "
    "structured messenger data."
)


def create_app() -> FastAPI:
    settings = APISettings()
    service = GroupScraperService(settings)

    app = FastAPI(
        title="Facebook Group Scraper API",
        description=API_DESCRIPTION,
        version="1.0.0",
        contact={
            "name": "fbchat-muqit",
            "url": "https://github.com/togashigreat/fbchat-muqit",
        },
    )
    app.include_router(create_router(service))

    @app.get("/healthz", tags=["Health"], summary="Basic health probe")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.state.settings = settings
    app.state.scraper_service = service
    return app


app = create_app()

__all__ = ["app", "create_app"]
