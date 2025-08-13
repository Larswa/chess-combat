# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies and Python packages in one layer
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache/pip

# Copy app code
COPY app ./app

# Copy migration script and VERSION.txt
COPY migrate_db.py ./
COPY VERSION.txt ./

# Add build timestamp (will be set during build)
ARG BUILD_TIMESTAMP
ENV BUILD_TIMESTAMP=${BUILD_TIMESTAMP}

# Expose port
EXPOSE 8000

# Set environment variables (override in docker run if needed)
ENV PYTHONUNBUFFERED=1

# Create startup script that runs migration then starts the app
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "Chess Combat - Starting container..."

# Run database migration
echo "Running database migration..."
if python3 migrate_db.py; then
    echo "Database migration completed successfully"
else
    echo "Database migration failed, but continuing to start application..."
    echo "The application will create tables automatically if possible"
fi

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF

RUN chmod +x /app/start.sh

# Start with migration then FastAPI app
CMD ["/app/start.sh"]
