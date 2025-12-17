# Wolf-Goat-Pig Backend Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Build Stage
# =============================================================================
# Use Python 3.12.8 to match Render deployment (render.yaml specifies PYTHON_VERSION: 3.12.8)
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
# Use Python 3.12 to match Render deployment
FROM python:3.12-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
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

# Create data directory (matches Render disk mount path)
RUN mkdir -p /opt/render/project/src/data logs && chown -R wgp:wgp /opt/render/project/src/data logs

# Health check (matches Render health check path: /ready)
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

# Use render-startup.py to match Render deployment exactly
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