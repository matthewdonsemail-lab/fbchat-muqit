"""FastAPI routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .models import GroupScrapeRequest, GroupScrapeResponse
from .service import GroupScraperService, ScraperError


def create_router(service: GroupScraperService) -> APIRouter:
    router = APIRouter(prefix="", tags=["Groups"])

    @router.post(
        "/groups/scrape",
        response_model=GroupScrapeResponse,
        summary="Scrape Facebook group or messenger thread posts",
        response_description="Scraped posts together with metadata.",
    )
    async def scrape_group(payload: GroupScrapeRequest) -> GroupScrapeResponse:
        """Run an on-demand scrape using the supplied configuration."""

        try:
            return await service.scrape_group(payload)
        except ScraperError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.post(
        "/groups/scrape/run",
        response_model=GroupScrapeResponse,
        include_in_schema=True,
        summary="Alias for /groups/scrape for parity with Apify actors",
    )
    async def scrape_group_run(payload: GroupScrapeRequest) -> GroupScrapeResponse:
        try:
            return await service.scrape_group(payload)
        except ScraperError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return router


__all__ = ["create_router"]
