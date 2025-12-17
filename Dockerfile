# Multi-stage Dockerfile for Weather Sensors MQTT Services
# Optimized for Docker Desktop + Portainer deployment

# Build stage

FROM python:3.12-slim AS builder

# Install build dependencies and tzdata
RUN apt-get update && apt-get install -y \
    gcc \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set working directory (creates /app with root ownership)
WORKDIR /app

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies as root (system-wide)
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Create appuser with explicit UID/GID (1000:1000 is standard)
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

# Set ownership of app directory
RUN chown -R appuser:appuser /app

# Switch to appuser
USER appuser

# Production stage

FROM python:3.12-slim AS production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies and tzdata
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY *.py ./
COPY entrypoint.sh ./

# Create required directories before copying config files
RUN mkdir -p config data logs

# Copy static configuration files (baked into image)
# Note: runtime config like local_sensors.json comes from volume mount
COPY config/broker_config.py ./config/
COPY config/mqtt_config.py ./config/
COPY config/logging_config.py ./config/
COPY config/protocol_categories.json ./config/
COPY config/rtl_433_protocols.json ./config/
COPY config/tracked_protocols.json ./config/

# Set ownership of all app directories
RUN chown -R appuser:appuser /app

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Switch to non-root user
USER appuser

# Expose any required ports (if needed for health checks)
EXPOSE 8080

# Health check for Portainer monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# No default CMD - let SERVICE environment variable control which service runs
# CMD ["republish"]

# Labels for Portainer organization
LABEL maintainer="karl@ktb.dev"
LABEL description="Weather Sensors and Smart Plugs MQTT Processing Services"
LABEL version="1.0.0"
LABEL service.type="mqtt-processor"