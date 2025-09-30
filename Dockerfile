# Multi-stage Dockerfile for auto-reviewer
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Development stage with additional tools
FROM base as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./
COPY requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create directories for data persistence
RUN mkdir -p /app/data/vector_db \
    /app/data/cache \
    /app/data/outputs \
    /app/data/uploads \
    && chown -R appuser:appuser /app/data

# Production stage
FROM base as production

# Copy requirements
COPY requirements.txt ./

# Install only production dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY pyproject.toml ./

# Install the package
RUN pip install .

# Create data directories and ensure proper ownership
RUN mkdir -p /app/data/vector_db \
    /app/data/cache \
    /app/data/outputs \
    /app/data/uploads \
    && chown -R appuser:appuser /app/data \
    && chown -R appuser:appuser /home/appuser

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import auto_reviewer; print('OK')" || exit 1

# Default command
CMD ["auto-reviewer", "--help"]

# Final stage selection based on build arg
FROM ${BUILD_TARGET:-production} as final