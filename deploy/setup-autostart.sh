#!/bin/bash
# Setup Auto-Start Services on Server
# This script configures systemd to automatically start Docker apps on boot

set -e

echo "=== Setting up Auto-Start Services ==="

# Copy systemd service file
echo "Installing systemd service..."
sudo cp systemd/docker-apps.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/docker-apps.service

# Make startup script executable
echo "Setting up startup script..."
chmod +x docker-apps-startup.sh

# Reload systemd daemon
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling docker-apps service..."
sudo systemctl enable docker-apps.service

# Check if Docker is enabled
echo "Ensuring Docker is enabled on boot..."
sudo systemctl enable docker

# Check if nginx is enabled
echo "Ensuring nginx is enabled on boot..."
sudo systemctl enable nginx

# Start the service now (if not already running)
echo "Starting docker-apps service..."
sudo systemctl start docker-apps.service

# Check status
echo "Checking service status..."
sudo systemctl status docker-apps.service --no-pager -l

echo ""
echo "=== Auto-Start Setup Complete ==="
echo ""
echo "Services configured to start on boot:"
echo "  ✓ docker.service"
echo "  ✓ nginx.service" 
echo "  ✓ docker-apps.service (your applications)"
echo ""
echo "To manually manage the service:"
echo "  sudo systemctl start docker-apps.service"
echo "  sudo systemctl stop docker-apps.service"
echo "  sudo systemctl restart docker-apps.service"
echo "  sudo systemctl status docker-apps.service"
echo ""
echo "Logs can be viewed with:"
echo "  sudo journalctl -u docker-apps.service -f"
echo "  tail -f /var/log/docker-apps-startup.log"
