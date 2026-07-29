# Command Nexus License Key Generator — Containerized API
# ==========================================================
# This Dockerfile builds a secure, production-ready container
# for the license key generation web service.
#
# Usage:
#   docker build -t command-nexus-keygen .
#   docker run -p 8000:8000 --env SECRET_KEY=<your-secret> command-nexus-keygen
#
# The container exposes a REST API for:
#   - Generating license keys (authenticated)
#   - Verifying license keys (public)
#   - Blacklisting leaked keys
#
# Security features:
#   - Non-root user
#   - Read-only root filesystem
#   - No shell access
#   - Distroless final image
#   - Secrets via environment variables only

# ---------------------------------------------------------------------------
# Stage 1: Builder
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY docker/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime (distroless for minimal attack surface)
# ---------------------------------------------------------------------------
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY license_key_generator.py .
COPY src/core/license_manager.py ./src/core/license_manager.py
COPY docker/api_server.py .

# Ensure Python can find packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/root/.local/lib/python3.12/site-packages:/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run as non-root (distroless runs as 65532:65532 by default)
USER 65532:65532

# The API server port
EXPOSE 8000

# No shell, no package manager, minimal attack surface
ENTRYPOINT ["python3", "-m", "uvicorn", "api_server:app"]
CMD ["--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
