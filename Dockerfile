# Log Parser Utility - Docker Image
# Runs the web UI in a container

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Install system dependencies (if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY src/web/requirements.txt /app/web-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/web-requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application code
COPY src/ /app/src/
COPY docs/ /app/docs/
COPY examples/ /app/examples/
COPY README.md /app/
COPY VERSION /app/

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')" || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--chdir", "/app/src/web", "app:app"]
