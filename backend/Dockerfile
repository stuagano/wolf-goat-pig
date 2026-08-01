# Wolf-Goat-Pig Backend Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Build Stage
# =============================================================================
# Pin the Python runtime used by Cloud Run.
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt requirements-local.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Production Stage
# =============================================================================
# Production Python runtime
FROM python:3.12-slim as production

# Install runtime dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r wgp && useradd -r -g wgp -s /bin/bash wgp

# Set work directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy application code
COPY --chown=wgp:wgp . .

# Ensure startup scripts are executable
RUN chmod +x startup.py render-startup.py

# Create runtime log directory
RUN mkdir -p logs && chown -R wgp:wgp logs

# Container health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/ready || exit 1

# Switch to non-root user
USER wgp

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8000

# Expose port
EXPOSE 8000

# Apply migrations, then start uvicorn.
CMD ["python", "render-startup.py"]

# =============================================================================
# Development Stage (optional)
# =============================================================================
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov

# Install git for development
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Switch back to wgp user
USER wgp

# Override environment for development
ENV ENVIRONMENT=development \
    AUTO_RELOAD=true \
    ENABLE_DOCS=true \
    LOG_LEVEL=DEBUG

# Development command with auto-reload
CMD ["python", "startup.py", "--environment=development", "--log-level=DEBUG"]