# Simple AI Manager Docker Build
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash aimanager

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY setup.py ./

# Install the application
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/artifacts /app/runs && \
    chown -R aimanager:aimanager /app

# Switch to non-root user
USER aimanager

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set environment defaults
ENV DATABASE_URL=sqlite:///./data/manager.db \
    ENVIRONMENT=production \
    DEBUG=false \
    LOG_LEVEL=INFO

# Start the application
CMD ["python", "-m", "cli.api_cli", "--host", "0.0.0.0", "--port", "8000"]