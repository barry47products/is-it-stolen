# Multi-stage build for minimal image size
# Note: python:3.13-slim currently has 1 known vulnerability in the Debian base
# For production, consider Dockerfile.chainguard using Wolfi-based images

# Builder stage - install dependencies
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies for psycopg2 and geoalchemy2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy only dependency files first (better layer caching)
COPY pyproject.toml poetry.lock* README.md ./

# Install dependencies (--only main for production)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root

# Copy application code for poetry install
COPY src ./src

# Install the application
RUN poetry install --only-root --no-interaction --no-ansi

# Final runtime stage
FROM python:3.13-slim

# Security labels
LABEL maintainer="Is It Stolen <noreply@isitstolen.com>" \
      version="1.0" \
      description="Is It Stolen WhatsApp Bot"

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code with correct ownership
COPY --chown=1000:1000 src ./src

# Create non-root user for security
RUN useradd -m -u 1000 appuser
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application with production settings
CMD ["uvicorn", "src.presentation.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
