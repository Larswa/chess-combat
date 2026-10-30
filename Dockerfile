# Build stage: full image with pip (and a compiler if a dependency lacks wheels)
FROM dhi.io/python:3.11.18-debian13-dev AS builder
WORKDIR /build
COPY requirements.txt ./
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

# Runtime stage: distroless-style (no shell, no pip), nonroot uid 65532
FROM dhi.io/python:3.11.18-debian13
WORKDIR /app

COPY --from=builder /deps /deps

# Copy app code, migration script, startup entrypoint and VERSION.txt
COPY app ./app
COPY migrate_db.py start.py VERSION.txt ./

# Add build timestamp (will be set during build)
ARG BUILD_TIMESTAMP
ENV BUILD_TIMESTAMP=${BUILD_TIMESTAMP}

EXPOSE 8000

# /deps holds the installed packages (no pip/site-packages in runtime image)
ENV PYTHONPATH=/deps:/app \
    PYTHONUNBUFFERED=1

USER 65532:65532

# start.py runs the migration (failure tolerated) then starts uvicorn; no shell needed
CMD ["python3", "/app/start.py"]
