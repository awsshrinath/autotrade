# Stage 1: The builder stage, to compile requirements
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies and pip-tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    && pip install --no-cache-dir pip-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-compiled requirements file
COPY requirements.txt .

# Set PATH for pip user installations during build
ENV PATH="/root/.local/bin:$PATH"

# Install PyTorch CPU version first (smaller and more compatible)
RUN pip install --no-cache-dir --user --no-warn-script-location torch --index-url https://download.pytorch.org/whl/cpu

# Install dependencies in builder stage
RUN pip install --no-cache-dir --user --no-warn-script-location -r requirements.txt

# Stage 2: The final application image
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && groupadd -g 1001 appgroup \
    && useradd -u 1001 -g appgroup -d /app -s /bin/bash appuser \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy requirements.txt for reference
COPY requirements.txt /app/requirements.txt

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/home/appuser/.local/lib/python3.10/site-packages:$PYTHONPATH

# Copy entrypoint and health check scripts first and make them executable
COPY entrypoint.sh /app/entrypoint.sh
COPY docker-healthcheck.sh /app/docker-healthcheck.sh
RUN chmod +x /app/entrypoint.sh /app/docker-healthcheck.sh

# Copy only necessary application code (exclude unnecessary files)
COPY runner/ /app/runner/
COPY stock_trading/ /app/stock_trading/
COPY options_trading/ /app/options_trading/
COPY futures_trading/ /app/futures_trading/
COPY dashboard_api/ /app/dashboard_api/
COPY gpt_runner/ /app/gpt_runner/
COPY config/ /app/config/
COPY strategies/ /app/strategies/
COPY utils/ /app/utils/
COPY services/ /app/services/
COPY mcp/ /app/mcp/
COPY main.py /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Declare the build argument
ARG RUNNER_SCRIPT

# Set default runner using the build argument if provided, otherwise default
ENV RUNNER_SCRIPT=${RUNNER_SCRIPT:-runner/main_runner.py}
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/entrypoint.sh"]