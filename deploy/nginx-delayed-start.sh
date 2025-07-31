#!/bin/bash
# Nginx Startup Script - handles timing issues with Docker containers

# Wait for Docker containers to be fully up
sleep 30

# Start nginx
systemctl start nginx

# If nginx fails to start, try again after containers are fully up
if ! systemctl is-active --quiet nginx; then
    echo "Nginx failed to start, waiting longer for containers..."
    sleep 60
    systemctl start nginx
fi
