"""Railway buildpack entrypoint.

This module allows Railway's Python buildpack to find a start command when
Docker is not used. It simply boots the FastAPI application that already ships
inside the fbchat_muqit_api package.
"""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    """Start the ASGI server using the FastAPI app."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "fbchat_muqit_api.main:app",
        host="0.0.0.0",
        port=port,
    )


if __name__ == "__main__":
    main()
