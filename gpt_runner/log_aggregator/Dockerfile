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

# Copy the gpt_runner directory into the container's root
COPY gpt_runner /gpt_runner

# Make port 8001 available to the world outside this container
EXPOSE 8001

# Define environment variables (can be overridden)
ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8001
ENV PYTHONPATH=/

# Run uvicorn server as a module from the root directory
WORKDIR /
CMD ["sh", "-c", "uvicorn gpt_runner.log_aggregator.main:app --host $FASTAPI_HOST --port $FASTAPI_PORT"] 