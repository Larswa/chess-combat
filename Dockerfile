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

# Copy VERSION.txt
COPY VERSION.txt ./

# Add build timestamp (will be set during build)
ARG BUILD_TIMESTAMP
ENV BUILD_TIMESTAMP=${BUILD_TIMESTAMP}

# Expose port
EXPOSE 8000

# Set environment variables (override in docker run if needed)
ENV PYTHONUNBUFFERED=1

# Start the FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
