"""Business logic for the HTTP API."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Iterable, List, Optional, Sequence
from urllib.parse import parse_qs, urlparse

from fbchat_muqit import Client
from fbchat_muqit.models.message import Message

from .config import APISettings
from .models import (
    AttachmentSummary,
    GroupScrapeRequest,
    GroupScrapeResponse,
    ScrapeStats,
    ScrapedPost,
)

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Raised when scraping cannot proceed."""

    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass(slots=True)
class CookieSource:
    path: Path
    is_temporary: bool = False


class GroupScraperService:
    """Orchestrates fbchat-muqit to expose an HTTP-friendly API."""

    def __init__(self, settings: APISettings) -> None:
        self.settings = settings

    async def scrape_group(self, payload: GroupScrapeRequest) -> GroupScrapeResponse:
        thread_id = self._extract_thread_id(payload.scrape_group_posts.group_url)
        if not thread_id:
            raise ScraperError("Unable to infer thread id from groupUrl", status_code=422)

        cookie_source = await self._resolve_cookie_source(payload.cookie)
        start = monotonic()
        try:
            async with Client(
                cookies_file_path=str(cookie_source.path),
                proxy=payload.proxy,
                log_level=self.settings.log_level,
            ) as client:
                items, next_cursor = await self._collect_messages(
                    client=client,
                    thread_id=thread_id,
                    payload=payload,
                )
        finally:
            if cookie_source.is_temporary:
                cookie_source.path.unlink(missing_ok=True)

        duration_ms = int((monotonic() - start) * 1000)
        stats = ScrapeStats(
            total_items=len(items),
            duration_ms=duration_ms,
            thread_id=thread_id,
            sort_type=payload.sort_type,
        )
        return GroupScrapeResponse(items=items, next_cursor=next_cursor, stats=stats)

    async def _collect_messages(
        self,
        client: Client,
        thread_id: str,
        payload: GroupScrapeRequest,
    ) -> tuple[List[ScrapedPost], Optional[int]]:
        until_ts = (
            int(payload.scrape_until.timestamp() * 1000)
            if payload.scrape_until
            else None
        )
        desired = payload.count
        min_delay = payload.min_delay or self.settings.default_min_delay
        max_delay = payload.max_delay or self.settings.default_max_delay
        if min_delay > max_delay:
            min_delay, max_delay = max_delay, min_delay

        remaining = desired
        before_cursor = payload.cursor
        aggregated: List[Message] = []
        reached_until = False

        while remaining > 0:
            batch = min(remaining, 50)
            messages = await client.fetch_thread_messages(
                thread_id=thread_id,
                message_limit=batch,
                before=before_cursor,
            )
            if not messages:
                break

            for message in messages:
                if until_ts and message.timestamp < until_ts:
                    reached_until = True
                    break
                aggregated.append(message)
                remaining -= 1
                if remaining <= 0:
                    break

            before_cursor = min(msg.timestamp for msg in messages) - 1
            if reached_until or remaining <= 0 or len(messages) < batch:
                break

            delay = random.uniform(min_delay, max_delay)
            await asyncio.sleep(delay)

        sender_ids = {msg.sender_id for msg in aggregated if msg.sender_id}
        sender_names = await self._fetch_sender_names(client, sender_ids)

        items = [
            self._message_to_post(message, sender_names)
            for message in aggregated
        ]
        items.sort(key=lambda item: item.timestamp, reverse=True)

        next_cursor = before_cursor if aggregated and not reached_until else None
        return items, next_cursor

    async def _fetch_sender_names(
        self, client: Client, sender_ids: Iterable[str]
    ) -> dict[str, str]:
        ids = [sid for sid in sender_ids if sid]
        if not ids:
            return {}
        try:
            info = await client.fetch_user_info(*ids)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to fetch sender metadata: %s", exc)
            return {}
        return {user_id: user.name for user_id, user in info.items()}

    def _message_to_post(
        self, message: Message, sender_names: dict[str, str]
    ) -> ScrapedPost:
        permalink = f"https://www.facebook.com/messages/t/{message.thread_id}/{message.id}"
        timestamp = datetime.fromtimestamp(message.timestamp / 1000, tz=UTC)
        attachments = [self._attachment_summary(att) for att in message.attachments or []]
        return ScrapedPost(
            id=message.id,
            thread_id=message.thread_id,
            author_id=message.sender_id,
            author_name=sender_names.get(message.sender_id),
            body=message.text,
            permalink=permalink,
            timestamp=timestamp,
            reaction_count=len(message.reaction or []),
            attachments=attachments,
        )

    @staticmethod
    def _attachment_summary(attachment) -> AttachmentSummary:
        url = getattr(getattr(attachment, "preview", None), "url", None)
        if not url:
            url = getattr(attachment, "playable_url", None) or getattr(
                attachment, "url", None
            )
        filename = getattr(attachment, "filename", None)
        return AttachmentSummary(
            type=getattr(getattr(attachment, "type", None), "value", None)
            or getattr(attachment, "type", None),
            url=url,
            filename=filename,
        )

    async def _resolve_cookie_source(
        self, cookies: Optional[Sequence[dict]]
    ) -> CookieSource:
        if cookies:
            fd, tmp_name = tempfile.mkstemp(prefix="fb-cookies-", suffix=".json")
            os.close(fd)
            path = Path(tmp_name)
            serialized = [
                cookie.model_dump(by_alias=True, exclude_none=True)
                if hasattr(cookie, "model_dump")
                else cookie
                for cookie in cookies
            ]
            path.write_text(
                json.dumps(serialized, ensure_ascii=False),
                encoding="utf-8",
            )
            return CookieSource(path=path, is_temporary=True)

        if self.settings.cookies_file_path:
            path = self.settings.cookies_file_path
            if not path.exists():
                raise ScraperError(
                    f"Cookies file not found at {path}", status_code=500
                )
            return CookieSource(path=path)

        raise ScraperError(
            "No cookies supplied. Provide cookie array or FB_COOKIES_FILE_PATH.",
            status_code=422,
        )

    @staticmethod
    def _extract_thread_id(group_url: str) -> Optional[str]:
        parsed = urlparse(group_url)
        if not parsed.netloc:
            return None
        path_parts = [part for part in parsed.path.split("/") if part]
        if "messages" in path_parts:
            try:
                idx = path_parts.index("t")
                return path_parts[idx + 1]
            except (ValueError, IndexError):
                pass
        if path_parts:
            last = path_parts[-1]
            if last.isdigit():
                return last
        query = parse_qs(parsed.query)
        for key in ("id", "group_id", "thread_id"):
            if key in query and query[key]:
                return query[key][0]
        digits = "".join(ch for ch in parsed.path if ch.isdigit())
        return digits or None


__all__ = ["GroupScraperService", "ScraperError"]
