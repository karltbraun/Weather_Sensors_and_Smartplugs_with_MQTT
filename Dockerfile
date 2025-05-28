FROM python:3.9-slim-bookworm

WORKDIR /app

# System dependencies and uv installation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy requirements first for better caching
COPY requirements.txt .

# Use uv to install dependencies
RUN uv pip install --system -r requirements.txt

COPY . .

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Use environment variables for configuration
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python", "src/republish_processed_sensors_main.py"]