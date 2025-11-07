# Multi-stage Dockerfile for Weather Sensors MQTT Services
# Optimized for Docker Desktop + Portainer deployment

# Build stage
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim AS production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY *.py ./
COPY entrypoint.sh ./

# Create required directories
RUN mkdir -p logs data && \
    chown -R appuser:appuser /app

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