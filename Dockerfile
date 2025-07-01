# Stage 1: The builder stage, to compile requirements
FROM python:3.10-slim as builder

WORKDIR /app

# Install pip-tools
RUN pip install pip-tools

# Copy only the requirements input file
COPY requirements.in .

# Compile the requirements.txt file
# This will generate a fully-pinned requirements.txt compatible with Python 3.10
RUN pip-compile requirements.in --output-file=requirements.txt --pip-args "--timeout=60"

# Stage 2: The final application image
FROM python:3.10-slim

WORKDIR /app

# Copy the generated requirements.txt from the builder stage
COPY --from=builder /app/requirements.txt .

# Install the pinned dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script first and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy the rest of the application code
COPY . .

# Set default runner (can be overridden in Kubernetes via ENV)
ENV PYTHONPATH=/app
ENV RUNNER_SCRIPT=runner/main_runner.py

ENTRYPOINT ["/app/entrypoint.sh"]