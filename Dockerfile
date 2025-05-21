FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG RUNNER_SCRIPT=runner/main_runner_combined.py
CMD ["sh", "-c", "python ${RUNNER_SCRIPT}"]
