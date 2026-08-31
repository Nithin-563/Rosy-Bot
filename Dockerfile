# Rosy - production Docker image (Railway-ready)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# System deps: ffmpeg for music/voice; git for yt-dlp updates.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer caching).
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip \
    && pip install ".[voice,web,pdf]" \
    || pip install .

# App files.
COPY . .

# Non-root user for safety.
RUN useradd --create-home rosy && chown -R rosy:rosy /app
USER rosy

EXPOSE 8080
CMD ["python", "-m", "rosy.main"]