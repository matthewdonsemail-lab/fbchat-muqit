"""Pydantic models shared by the service and the HTTP layer."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CookieEntry(BaseModel):
    """Single browser cookie item."""

    key: str = Field(..., description="Cookie name, e.g. c_user")
    value: str = Field(..., description="Cookie value")
    domain: str = Field(..., description="Domain attribute of the cookie")
    path: str = Field(default="/", description="Path attribute for the cookie")
    expires: Optional[int] = Field(
        default=None,
        description="Unix timestamp (seconds) for when the cookie expires",
    )
    httpOnly: Optional[bool] = Field(
        default=None,
        description="Whether the cookie is HTTP only, mirrors browser exports",
    )
    secure: Optional[bool] = Field(
        default=None,
        description="Whether the cookie requires HTTPS",
    )

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class SortType(str, Enum):
    """Supported Facebook group feed sort types."""

    MOST_RELEVANT = "most_relevant"
    RECENT_ACTIVITY = "recent_activity"
    NEW_POSTS = "new_posts"


class ScrapeGroupPostsOptions(BaseModel):
    """Options describing which group to scrape."""

    group_url: str = Field(
        ..., alias="groupUrl", description="URL of the Facebook group or thread"
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class GroupScrapeRequest(BaseModel):
    """POST payload accepted by the scraper endpoint."""

    cookie: Optional[List[CookieEntry]] = Field(
        default=None,
        description=(
            "Optional array of cookies for per-request authentication. "
            "When omitted the service falls back to FB_COOKIES_FILE_PATH."
        ),
    )
    scrape_group_posts: ScrapeGroupPostsOptions = Field(
        ..., alias="scrapeGroupPosts", description="Group scraping configuration"
    )
    count: int = Field(
        default=25,
        ge=1,
        le=200,
        description="Maximum number of messages/posts to return",
    )
    cursor: Optional[int] = Field(
        default=None,
        description=(
            "Pagination cursor. When provided it is interpreted as a millisecond "
            "timestamp and becomes the 'before' parameter for the next page."
        ),
    )
    sort_type: SortType = Field(
        default=SortType.RECENT_ACTIVITY,
        alias="sortType",
        description="Desired Facebook sort order. Used for descriptive metadata.",
    )
    scrape_until: Optional[datetime] = Field(
        default=None,
        alias="scrapeUntil",
        description="ISO timestamp. Messages older than this are ignored.",
    )
    min_delay: Optional[float] = Field(
        default=None,
        alias="minDelay",
        description="Minimum delay (in seconds) between pagination calls.",
    )
    max_delay: Optional[float] = Field(
        default=None,
        alias="maxDelay",
        description="Maximum delay (in seconds) between pagination calls.",
    )
    proxy: Optional[str] = Field(
        default=None,
        description="Optional HTTPS proxy URL passed to fbchat-muqit Client.",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @model_validator(mode="after")
    def validate_delays(self) -> "GroupScrapeRequest":
        min_delay = self.min_delay
        max_delay = self.max_delay
        if min_delay is not None and max_delay is not None and min_delay > max_delay:
            raise ValueError("minDelay cannot be greater than maxDelay")
        return self


class AttachmentSummary(BaseModel):
    """Minimal description of a messenger attachment."""

    type: Optional[str] = Field(None, description="Attachment type name")
    url: Optional[str] = Field(
        None, description="Preview or downloadable URL when available"
    )
    filename: Optional[str] = Field(
        None, description="Original filename for file-like attachments"
    )


class ScrapedPost(BaseModel):
    """Single scraped messenger item."""

    id: str = Field(..., description="Message identifier")
    thread_id: str = Field(..., description="Thread the message belongs to")
    author_id: str = Field(..., description="Sender Facebook ID")
    author_name: Optional[str] = Field(
        default=None, description="Display name of the sender when known"
    )
    body: Optional[str] = Field(None, description="Textual body of the message")
    permalink: Optional[str] = Field(
        None,
        description="Best-effort permalink pointing to the message inside Messenger",
    )
    timestamp: datetime = Field(
        ..., description="Message timestamp converted to an aware datetime"
    )
    reaction_count: int = Field(0, description="Number of reactions on the message")
    attachments: List[AttachmentSummary] = Field(
        default_factory=list, description="Lightweight attachment metadata"
    )


class ScrapeStats(BaseModel):
    """Execution metadata returned to clients."""

    total_items: int = Field(..., description="Total number of items returned")
    duration_ms: int = Field(..., description="How long the scrape took in ms")
    thread_id: str = Field(..., description="Thread ID resolved from the group URL")
    sort_type: SortType = Field(..., description="Sort type requested by caller")


class GroupScrapeResponse(BaseModel):
    """Response envelope for the scrape endpoint."""

    items: List[ScrapedPost] = Field(..., description="Scraped posts/messages")
    next_cursor: Optional[int] = Field(
        None,
        alias="nextCursor",
        description=(
            "Timestamp cursor to resume scraping. `null` indicates no further data."
        ),
    )
    stats: ScrapeStats = Field(..., description="Execution metadata")

    model_config = ConfigDict(populate_by_name=True)


__all__ = [
    "AttachmentSummary",
    "CookieEntry",
    "GroupScrapeRequest",
    "GroupScrapeResponse",
    "ScrapeGroupPostsOptions",
    "ScrapeStats",
    "ScrapedPost",
    "SortType",
]
