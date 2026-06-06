# Use an official, lightweight Python base image
FROM python:3.11-slim

# Set system-level environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establish the working directory inside the container
WORKDIR /workspace

# Install system dependencies needed for compiling certain Python wheels if necessary
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker's caching layer
COPY requirements.txt .

# Install Python packages directly into the global container space
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the workspace
COPY . .

# Expose port 8000 so FastAPI can accept traffic from outside the container
EXPOSE 8000

# Command to execute your backend application via Uvicorn
CMD ["python", "main.py"]