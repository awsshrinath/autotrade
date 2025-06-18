FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script first and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY . .

# Set default runner (can be overridden in Kubernetes via ENV)
ENV PYTHONPATH=/app
ENV RUNNER_SCRIPT=runner/main_runner.py

ENTRYPOINT ["/app/entrypoint.sh"]