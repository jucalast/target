FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/shared/requirements.txt /app/shared_requirements.txt
COPY backend/nlp_processor/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/shared_requirements.txt -r /app/requirements.txt

# Install spaCy model
RUN python -m spacy download pt_core_news_sm

# Copy the application code
COPY backend/nlp_processor /app
COPY backend/shared /app/shared

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
