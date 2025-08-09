FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pydantic-settings

# Copy application code
COPY app/ ./app/
COPY main.py .
COPY alembic.ini .
COPY migrations/ ./migrations/

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs /app/static

# Create non-root user
RUN useradd -m -u 1000 assetdna && \
    chown -R assetdna:assetdna /app

# Switch to non-root user
USER assetdna

# Expose port
EXPOSE 10001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10001/health || exit 1

# Run application
CMD ["python", "main.py"]