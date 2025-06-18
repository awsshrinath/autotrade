# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /

# Copy the requirements file
COPY gpt_runner/log_aggregator/requirements.txt /app/requirements.txt

# Set the working directory to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application's code into the container at /app
COPY . /app

# Make port 8001 available to the world outside this container
EXPOSE 8001

# Define environment variables (can be overridden)
ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8001
ENV PYTHONPATH=/app

# Run uvicorn server as a module
CMD ["python", "-m", "uvicorn", "gpt_runner.log_aggregator.main:app", "--host", "0.0.0.0", "--port", "8001"] 