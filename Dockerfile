FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md LICENSE.md LICENSE-BSD.md ./
COPY fbchat_muqit ./fbchat_muqit
COPY fbchat_muqit_api ./fbchat_muqit_api

RUN pip install --upgrade pip \
    && pip install --no-cache-dir '.[api]'

COPY . .

RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser /app
USER appuser

EXPOSE 8000
ENV PORT=8000

CMD ["sh", "-c", "uvicorn fbchat_muqit_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
