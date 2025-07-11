# Use official Python image
FROM python:3.10-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and bot files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start the bot
CMD ["python", "music_bot.py"]
