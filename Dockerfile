# Rosy — production image for Railway (or any container host).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: ffmpeg for music/voice, build tools for asyncpg/cryptography.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        gcc \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml README.md ./
COPY rosy ./rosy
COPY migrations ./migrations
COPY alembic.ini ./

RUN pip install --no-cache-dir . 

# Health check for Railway.
COPY docker_healthcheck.py .
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python docker_healthcheck.py

# Run migrations then start the bot.
CMD ["sh", "-c", "alembic upgrade head && python -m rosy.main"]
