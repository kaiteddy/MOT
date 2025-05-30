# Multi-stage Docker build for MOT OCR System
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads results logs

# Create non-root user
RUN groupadd -r motocr && useradd -r -g motocr motocr
RUN chown -R motocr:motocr /app
USER motocr

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "run.py"]

# Development stage
FROM base as development

USER root

# Install development dependencies
RUN pip install pytest pytest-asyncio pytest-cov black flake8 mypy

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

USER motocr

# Override command for development
CMD ["python", "run.py"]

# Production stage
FROM base as production

# Install curl for health checks
USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
USER motocr

# Production optimizations
ENV API_DEBUG=false \
    LOG_LEVEL=INFO \
    MAX_CONCURRENT_REQUESTS=10

# Run the application
CMD ["python", "run.py"]
