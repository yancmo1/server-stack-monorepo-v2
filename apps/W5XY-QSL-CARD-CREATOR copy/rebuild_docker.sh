#!/bin/bash

# QSL Card Creator - Docker Rebuild Script
# Quickly rebuild and restart the Docker container for testing

echo "🐳 QSL Card Creator - Docker Rebuild"
echo "======================================="

# Stop and remove existing container
echo "🛑 Stopping existing container..."
docker stop qsl-card-creator 2>/dev/null || true
docker rm qsl-card-creator 2>/dev/null || true

# Build new image
echo "🔨 Building Docker image..."
docker build -t qsl-card-creator .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

# Start new container with database volume mount
echo "🚀 Starting new container..."
docker run -d --name qsl-card-creator -p 5001:5001 \
  -v "/Users/yancyshepherd/SyncthingFolders/Log4OM-Database/Log4OM db.SQLite":/app/"Log4OM db.SQLite" \
  qsl-card-creator

if [ $? -eq 0 ]; then
    echo "✅ Container started successfully!"
    echo "🌐 Access at: http://localhost:5001"
    echo ""
    echo "📊 Container status:"
    docker ps | grep qsl-card-creator
else
    echo "❌ Failed to start container!"
    exit 1
fi
