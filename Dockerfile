# Multi-stage build for production
FROM python:3.11-slim-bullseye as builder

WORKDIR /app

# Install build dependencies and security updates
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim-bullseye

WORKDIR /app

# Install runtime dependencies and security updates
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app ./app
COPY ./migrations ./migrations
COPY alembic.ini .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p logs && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/document/healthCheck', timeout=5)"

# Run with gunicorn for production
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info"]
