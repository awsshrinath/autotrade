# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to get access to runner module
COPY . .

# Set Python path to include runner module
ENV PYTHONPATH="/app:/app/runner:$PYTHONPATH"

# Create __init__.py files for all necessary directories to ensure they are importable
RUN for dir in runner gpt_runner runner/capital runner/enhanced_logging runner/indicators runner/market_data runner/options runner/production runner/utils gpt_runner/rag gpt_runner/log_aggregator; do \
        if [ -d "$dir" ] && [ ! -f "$dir/__init__.py" ]; then \
            touch "$dir/__init__.py"; \
        fi; \
    done

# Expose port 8000 to the outside world
EXPOSE 8000

# Set working directory to dashboard_api for the application
WORKDIR /app/dashboard_api

# Command to run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 