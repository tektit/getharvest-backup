# Multi-stage build for Harvest backup tool
FROM python:3.13-alpine AS builder

WORKDIR /app

# Install uv via pip
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Copy source code
COPY src/ ./src/

# Install dependencies and package from lock file (no dev dependencies)
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-dev --frozen

# Final stage
FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code (package is installed in editable mode)
COPY --from=builder /app/src /app/src

WORKDIR /

ENV PATH="/app/.venv/bin:$PATH"

# Expose Harvest PAT environment variable
ENV HARVEST_PAT=

VOLUME ["/backup"]

# Run the application
ENTRYPOINT ["harvest-backup"]
