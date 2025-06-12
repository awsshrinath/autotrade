# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY gpt_runner/log_aggregator/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container at /app
COPY gpt_runner/log_aggregator/ .

# Set the python path to include the app directory
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Make port 8001 available to the world outside this container
EXPOSE 8001

# Define environment variables (can be overridden)
ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8001

# Run uvicorn server
CMD ["uvicorn", "main:app", "--host", "$FASTAPI_HOST", "--port", "$FASTAPI_PORT"] 