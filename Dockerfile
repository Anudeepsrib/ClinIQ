# Stage 1: Builder
FROM python:3.11.9-slim-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final Runtime
FROM python:3.11.9-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install curl for HEALTHCHECK and required runtime dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code and set ownership
COPY --chown=appuser:appuser . .

# Create directory for vector db (if needed locally, though K8s should use PVCs)
RUN mkdir -p data/vector_db && chown -R appuser:appuser data/vector_db && chmod 777 data/vector_db

# Switch to non-root user
USER appuser

EXPOSE 8000

# Healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
