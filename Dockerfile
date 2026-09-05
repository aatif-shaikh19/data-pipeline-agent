# ==============================================================================
# Pipeline Guardian - Production Dockerfile
# ==============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies needed for compiling/building libraries (e.g. psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create a non-root user for security (OWASP Best Practice)
RUN useradd -u 1000 appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Launch uvicorn dynamically binding to Railway's assigned $PORT (or 8000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
