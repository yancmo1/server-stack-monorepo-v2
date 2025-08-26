# QSL Card Creator Web App - Dockerfile

# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including Pillow via system package for ARM)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libjpeg-dev \
        zlib1g-dev \
        libsqlite3-0 \
        poppler-utils \
        libxml2-dev \
        libxslt1-dev \
        libffi-dev \
        gcc \
        g++ \
        python3-dev \
        python3-pil \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# Use ARM-optimized requirements if on ARM architecture
COPY web_requirements*.txt ./
RUN if [ "$(uname -m)" = "armv7l" ] || [ "$(uname -m)" = "aarch64" ]; then \
        echo "ARM detected, using ARM-optimized requirements"; \
        pip install --no-cache-dir -r web_requirements_arm.txt; \
    else \
        echo "x86 detected, using full requirements"; \
        pip install --no-cache-dir -r web_requirements.txt; \
    fi

# Copy application code (excluding backup_files and other unnecessary files)
COPY . .

# Expose Flask port used by web_app (default 5553; can be overridden by QSL_WEB_PORT)
EXPOSE 5553

# Set environment variable for Flask (optional, for production use)
# ENV FLASK_ENV=production

# Run the Flask app
CMD ["python", "web_app.py"]
