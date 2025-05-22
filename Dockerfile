FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set default runner (can be overridden in Kubernetes via ENV)
ENV PYTHONPATH=/app
ENV RUNNER_SCRIPT=runner/main_runner_combined.py

# Shell form CMD allows env var substitution
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]