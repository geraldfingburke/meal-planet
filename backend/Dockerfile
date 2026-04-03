# ── Base stage ──────────────────────────────────────────────
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# ── Worker stage (adds Playwright browsers) ────────────────
FROM base AS worker

RUN pip install --no-cache-dir playwright google-genai && \
    playwright install --with-deps chromium
