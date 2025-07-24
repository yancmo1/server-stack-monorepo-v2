FROM python:3.11-slim

# Install system dependencies including Chromium browser
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    chromium \
    chromium-driver \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for compatibility
RUN ln -sf /usr/bin/chromium /usr/bin/google-chrome \
    && ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY improved_price_tracker.py .
COPY cruise_config.json .
COPY web_interface.py .

# Create directories for data persistence
RUN mkdir -p /app/data /app/logs

# Set environment variables for Chrome/Chromium in container
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Expose port for web interface
EXPOSE 5551

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5551/health || exit 1

# Default command runs the web interface
CMD ["python", "web_interface.py"]