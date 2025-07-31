FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/shared/requirements.txt /app/shared_requirements.txt
COPY backend/etl_pipeline/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/shared_requirements.txt -r /app/requirements.txt

# Create cache directory
RUN mkdir -p /app/cache

# Copy the application code
COPY backend/etl_pipeline /app
COPY backend/shared /app/shared

# Command to run the ETL pipeline
CMD ["python", "-m", "app.main"]
