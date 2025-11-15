"""Configuration helpers for the HTTP API."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    cookies_file_path: Optional[Path] = Field(
        default=None,
        alias="FB_COOKIES_FILE_PATH",
        description=(
            "Absolute path to a JSON file that contains a list of Facebook cookies. "
            "Used when requests do not provide a per-call cookie array."
        ),
    )
    default_min_delay: float = Field(
        default=0.5,
        alias="FB_DEFAULT_MIN_DELAY",
        description="Default minimum delay (in seconds) between pagination requests.",
    )
    default_max_delay: float = Field(
        default=2.0,
        alias="FB_DEFAULT_MAX_DELAY",
        description="Default maximum delay (in seconds) between pagination requests.",
    )
    log_level: str = Field(
        default="INFO",
        alias="FB_LOG_LEVEL",
        description="Log level passed to fbchat-muqit client instances.",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "extra": "ignore",
    }


__all__ = ["APISettings"]
