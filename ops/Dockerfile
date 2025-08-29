# Multi-stage Dockerfile for AI Manager

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim as production

# Create non-root user
RUN useradd --create-home --shell /bin/bash manager

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=manager:manager src/ src/
COPY --chown=manager:manager pyproject.toml .
COPY --chown=manager:manager README.md .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create directories
RUN mkdir -p /app/runs /app/artifacts /app/logs && \
    chown -R manager:manager /app

# Switch to non-root user
USER manager

# Environment variables
ENV PYTHONPATH=/app/src
ENV MANAGER_DB_URL=sqlite:///./manager.db
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "manager.api.http:app", "--host", "0.0.0.0", "--port", "8000"]