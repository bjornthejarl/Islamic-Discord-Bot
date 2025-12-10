# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        ffmpeg \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories for the bot
RUN mkdir -p src/data/economy/users src/data/economy/transactions src/data/profiles src/data/shop

# Extract audio files from zip if it exists
RUN if [ -f src/audio.zip ]; then \
        mkdir -p src/audio && \
        unzip -o src/audio.zip -d src/ && \
        rm src/audio.zip; \
    fi

# Set the entry point
CMD ["python", "bot.py"]