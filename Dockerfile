# Development runtime image with volume mounting
FROM python:3.12-slim-bookworm

# Install system dependencies
# Add Node.js 20.x LTS, nginx and development tools
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    gcc g++ git make \
    ffmpeg \
    supervisor \
    nginx \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv using the official method
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container to /app
WORKDIR /app

# Expose nginx port only (nginx will proxy to frontend:8502 and api:5055)
EXPOSE 8899

# Create necessary directories
RUN mkdir -p /app/data /var/log/supervisor /etc/supervisor/conf.d

# Runtime API URL Configuration
# The API_URL environment variable can be set at container runtime to configure
# where the frontend should connect to the API. This allows the same Docker image
# to work in different deployment scenarios without rebuilding.
#
# If not set, the system will auto-detect based on incoming requests.
# Set API_URL when using reverse proxies or custom domains.
#
# Example: docker run -e API_URL=https://your-domain.com/api ...

# Start supervisor to manage processes
# Note: supervisord.conf should be mounted from host at /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
