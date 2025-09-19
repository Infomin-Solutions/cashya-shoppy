# Multi-stage build for production with uv
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Install uv with pinned version
COPY --from=ghcr.io/astral-sh/uv:0.2.26 /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies to /opt/venv using uv sync (prod only, no dev group)
RUN uv venv /opt/venv \
    && . /opt/venv/bin/activate \
    && uv sync --frozen
ENV PATH="/opt/venv/bin:$PATH"

# Production stage
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

COPY . /app
WORKDIR /app

# Create data directory structure for database and media files
RUN mkdir -p /app/data/media

# Make docker-entrypoint.sh executable
RUN chmod +x docker/prod/docker-entrypoint.sh

# Declare volume for persistent data (database and media files)
# Recommended volume name: cashya-shoppy-data
VOLUME ["/app/data"]

# Add label with recommended volume name
LABEL volume.data.name="cashya-shoppy-data"
LABEL volume.data.path="/app/data"
LABEL volume.data.description="Contains SQLite database and media files"

EXPOSE 8000

CMD ["./docker/prod/docker-entrypoint.sh"]
