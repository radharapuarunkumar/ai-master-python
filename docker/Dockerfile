# ===========================================================================
# AI Master Python — Multi-stage Dockerfile
# ===========================================================================
# Build:  docker build -f docker/Dockerfile -t ai-master-python .
# Run:    docker run -p 8000:8000 --env-file .env ai-master-python
# ===========================================================================

# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# System deps required to compile some wheels (asyncpg, Pillow, weasyprint)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libffi-dev \
        libjpeg62-turbo-dev \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual-env so we can copy it cleanly
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml ./
# Install only production dependencies (no dev extras)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .


# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

LABEL maintainer="AI Master Team" \
      description="AI Master Python — AI-powered Python learning platform"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Default to production; override in docker-compose.dev.yml
    APP_ENV=production

# Runtime-only system libraries (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built virtual-env from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user for security
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /home/appuser/app

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Health check — hit the FastAPI health endpoint every 30s
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
