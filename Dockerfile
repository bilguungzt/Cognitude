FROM python:3.11-slim

# Install security updates and curl for healthcheck
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Create non-root user
RUN groupadd -r cognitude && useradd -r -g cognitude cognitude

# Install dependencies
COPY requirements.txt .
COPY alembic.ini .
COPY alembic /code/alembic
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /code/app
COPY ./scripts /code/scripts
COPY debug_api_errors.py /code/debug_api_errors.py

# Change ownership to non-root user
RUN chown -R cognitude:cognitude /code

# Switch to non-root user
USER cognitude

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
