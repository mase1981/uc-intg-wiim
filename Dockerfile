FROM python:3.11-slim

LABEL org.opencontainers.image.title="WiiM Integration for Unfolded Circle Remote Two"
LABEL org.opencontainers.image.description="Integration for controlling WiiM audio devices"
LABEL org.opencontainers.image.vendor="Meir Miyara"
LABEL org.opencontainers.image.source="https://github.com/mase1981/uc-intg-wiim"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and user
RUN groupadd -r wiim && useradd -r -g wiim -d /app -s /bin/bash wiim
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY driver.json .
COPY uc_intg_wiim/ ./uc_intg_wiim/

# Create config directory
RUN mkdir -p /app/config && chown -R wiim:wiim /app

# Switch to non-root user
USER wiim

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${UC_INTEGRATION_HTTP_PORT:-9090}/health || exit 1

# Expose port
EXPOSE 9090

# Environment variables
ENV UC_INTEGRATION_HTTP_PORT=9090
ENV UC_CONFIG_HOME=/app/config
ENV PYTHONPATH=/app

# Run the integration
CMD ["python", "-m", "uc_intg_wiim.driver"]