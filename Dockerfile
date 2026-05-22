# Use a lightweight python base image
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Set environment variables
# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (if any are needed in the future, e.g., git, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY main.py .
COPY src/ ./src/
COPY data/ ./data/
COPY relay/ ./relay/

# Create logs directory and ensure it has write permissions
RUN mkdir -p logs && chmod 777 logs

# Run as non-root user for security best practices
RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

# Set run command
CMD ["python", "main.py"]
