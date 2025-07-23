# Stage 1: The builder stage, to compile requirements
FROM python:3.10-alpine as builder

WORKDIR /app

# Install build dependencies and pip-tools
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    && pip install --no-cache-dir pip-tools

# Copy only the requirements input file
COPY requirements.in .

# Compile the requirements.txt file
RUN pip-compile requirements.in --output-file=requirements.txt --pip-args "--timeout=60"

# Install dependencies in builder stage
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: The final application image
FROM python:3.10-alpine

WORKDIR /app

# Install runtime dependencies only
RUN apk add --no-cache \
    curl \
    && addgroup -g 1001 -S appgroup \
    && adduser -u 1001 -S appuser -G appgroup

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

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