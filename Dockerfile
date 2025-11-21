# Dockerfile for Django, Celery, and Redis
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . /app/

# Collect static files (optional, for production)
# RUN python manage.py collectstatic --noinput

# Default command (override in docker-compose)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "AIModelBackend.asgi:application"]
