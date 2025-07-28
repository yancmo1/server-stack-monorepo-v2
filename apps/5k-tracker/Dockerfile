FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads/photos

# Create non-root user for security
RUN useradd -m -u 1000 racetracker && chown -R racetracker:racetracker /app
USER racetracker

EXPOSE 5011

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5554/ || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5011", "--workers", "2", "--timeout", "60", "app:app"]
