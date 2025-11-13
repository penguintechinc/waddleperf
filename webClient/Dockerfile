# Multi-stage build for webClient (unified API + Frontend)

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Python API with embedded frontend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    wget \
    && groupadd -g 1000 waddleperf \
    && useradd -m -u 1000 -g waddleperf waddleperf \
    && rm -rf /var/lib/apt/lists/*

# Copy API requirements and install
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy API application
COPY api/ ./

# Copy built frontend files to static directory
COPY --from=frontend-builder /app/frontend/dist ./static/

# Set ownership
RUN chown -R waddleperf:waddleperf /app

# Switch to non-root user
USER waddleperf

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1

# Environment defaults
ENV PORT=5000 \
    WORKERS=4 \
    WORKER_CLASS=eventlet \
    TIMEOUT=120 \
    LOG_LEVEL=info

# Run with gunicorn and SocketIO support
CMD gunicorn --bind 0.0.0.0:${PORT} --workers ${WORKERS} --worker-class ${WORKER_CLASS} --timeout ${TIMEOUT} --log-level ${LOG_LEVEL} "app:app"
