# Multi-stage Dockerfile for AI Manager System
# Optimized for production with security, performance, and size considerations

# Stage 1: Base Python image with system dependencies
FROM python:3.11-slim-bookworm as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies and security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1001 aimanager \
    && useradd --uid 1001 --gid aimanager --shell /bin/bash --create-home aimanager

# Set work directory
WORKDIR /app

# Stage 2: Dependencies installation
FROM base as dependencies

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Development environment (for testing and development)
FROM dependencies as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY --chown=aimanager:aimanager . .

# Install package in development mode
RUN pip install -e .

# Switch to non-root user
USER aimanager

# Expose port
EXPOSE 8000

# Development command
CMD ["python", "-m", "cli.api_cli", "--dev", "--host", "0.0.0.0", "--port", "8000"]

# Stage 4: Testing environment
FROM development as testing

# Switch back to root for test setup
USER root

# Install additional testing tools
RUN pip install pytest-cov pytest-xdist pytest-timeout locust

# Copy test configurations (if they exist)
# COPY pytest.ini .coveragerc ./

# Create test directories
RUN mkdir -p /app/test-results /app/coverage-reports

# Switch back to non-root user
USER aimanager

# Run tests command
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=html:/app/coverage-reports/", "--junit-xml=/app/test-results/results.xml"]

# Stage 5: Production build
FROM base as builder

# Copy requirements (production only)
COPY requirements.txt .

# Install production dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Build the package
RUN pip install --user .

# Stage 6: Production runtime
FROM python:3.11-slim-bookworm as production

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/aimanager/.local/bin:$PATH" \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 aimanager \
    && useradd --uid 1001 --gid aimanager --shell /bin/bash --create-home aimanager

# Copy Python packages from builder
COPY --from=builder --chown=aimanager:aimanager /root/.local /home/aimanager/.local

# Copy application code (minimal)
WORKDIR /app
COPY --from=builder --chown=aimanager:aimanager /src ./src/
COPY --from=builder --chown=aimanager:aimanager /cli ./cli/
COPY --from=builder --chown=aimanager:aimanager /setup.py ./

# Copy configuration files
COPY --chown=aimanager:aimanager .env.example .env

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/artifacts /app/runs && \
    chown -R aimanager:aimanager /app

# Switch to non-root user
USER aimanager

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["python", "-m", "cli.api_cli", "--host", "0.0.0.0", "--port", "8000"]

# Note: Monitoring stage removed for simplified deployment
# Can be re-added later when monitoring directory is created
