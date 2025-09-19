FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Install uv with pinned version
COPY --from=ghcr.io/astral-sh/uv:0.2.26 /uv /bin/uv

WORKDIR /app

# Copy dependency file first for better caching
COPY pyproject.toml ./

RUN uv venv /opt/venv \
    && . /opt/venv/bin/activate \
    && uv sync --group dev

# Now copy the rest of the project
COPY . /app

ENV PATH="/opt/venv/bin:$PATH"

# Create data directory structure for database and media files
RUN mkdir -p /app/data/media

# Make run.sh executable
RUN chmod +x docker/dev/docker-entrypoint.sh

# Declare volume for persistent data (database and media files)
# Recommended volume name: cashya-shoppy-data
VOLUME ["/app/data"]

# Add label with recommended volume name
LABEL volume.data.name="cashya-shoppy-data"
LABEL volume.data.path="/app/data"
LABEL volume.data.description="Contains SQLite database and media files"

EXPOSE 8000
EXPOSE 5678

CMD ["./docker/dev/docker-entrypoint.sh"]
