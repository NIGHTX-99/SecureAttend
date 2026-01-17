# Client Dockerfile for SecureAttend (optional - for containerized client)

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy client code
COPY client/ ./client/
COPY backend/ ./backend/  # Needed for Challenge import

# Create data directory
RUN mkdir -p /app/data

# Default command
CMD ["python", "-m", "client.ui.cli", "--help"]
