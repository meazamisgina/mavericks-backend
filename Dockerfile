# Foundation: Use Python 3.12
FROM python:3.12-slim

# Install Linux tools for Postgres and AI libraries
RUN apt-get update && apt-get install -y \
    libpq-dev gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up the app directory
WORKDIR /app

# Install dependencies first (better for speed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Django project files
COPY . .

# Hugging Face requires port 7860
EXPOSE 7860

# Run migrations and start the server
# Note: replace 'mitumbaesales' with your actual folder name if different
CMD python manage.py migrate && \
    gunicorn mitumbaesales.wsgi:application --bind 0.0.0.0:7860