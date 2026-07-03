# Start from official Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies MediaPipe needs
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for faster rebuilds)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your project files
COPY . .

# Expose port 5000 (your Flask API port)
EXPOSE 5000

# Command to run when container starts
CMD ["python3", "app.py"]