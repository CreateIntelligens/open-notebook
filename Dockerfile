FROM node:22-bookworm-slim AS builder
WORKDIR /opt/frontend
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm run build

# Dockerfile - Works for both development (with volumes) and production (standalone)
FROM python:3.12-slim-bookworm AS runner

# Install uv using the official method
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install runtime system dependencies
# Add Node.js 20.x LTS for running frontend
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    ffmpeg \
    supervisor \
    gnupg \
    ca-certificates \
    openssl \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && curl -fsSL https://nginx.org/keys/nginx_signing.key -o /tmp/nginx_signing.key \
    && gpg --dearmor --output /usr/share/keyrings/nginx-archive-keyring.gpg /tmp/nginx_signing.key \
    && echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] https://nginx.org/packages/mainline/debian bookworm nginx" > /etc/apt/sources.list.d/nginx.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nginx=1.31.7-1~bookworm \
    && nginx -v \
    && rm -rf /var/lib/apt/lists/* /tmp/nginx_signing.key

COPY --from=builder /opt/frontend /opt/frontend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_SYNC=1 \
    VIRTUAL_ENV=/app/.venv

# Set the working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/data /var/log/supervisor /app/ssl

# Expose ports for Frontend, API, and nginx
EXPOSE 8502 5055 8899

# Copy supervisord configuration
# This will be overridden by volume mount in docker-compose, but needed for standalone use
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Note: In docker-compose, volumes (.:/app) will provide all source code
# For standalone usage (docker run), mount your code or build a production image separately

# Default command
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
