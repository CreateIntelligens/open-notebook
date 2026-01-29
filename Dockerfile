# Dockerfile - Works for both development (with volumes) and production (standalone)
FROM python:3.12-slim-bookworm

# Install uv using the official method
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install runtime system dependencies
# Add Node.js 20.x LTS for running frontend
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    ffmpeg \
    supervisor \
    nginx \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

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
