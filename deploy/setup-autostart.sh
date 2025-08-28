#!/bin/bash
# Setup Auto-Start Services on Server
# This script configures systemd to automatically start Docker apps on boot

set -e

echo "=== Setting up Auto-Start Services ==="

# Copy systemd service files
echo "Installing systemd services..."
sudo cp systemd/docker-apps.service /etc/systemd/system/
sudo cp systemd/nginx-delayed.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/docker-apps.service
sudo chmod 644 /etc/systemd/system/nginx-delayed.service

# Make startup scripts executable
echo "Setting up startup scripts..."
chmod +x docker-apps-startup.sh
chmod +x nginx-delayed-start.sh

# Reload systemd daemon
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Disable any conflicting services first
echo "Stopping any conflicting services..."
sudo systemctl stop docker-apps.service || true
sudo systemctl stop nginx-delayed.service || true
sudo systemctl stop nginx.service || true

# Enable the services to start on boot
echo "Enabling docker-apps service..."
sudo systemctl enable docker-apps.service

echo "Enabling nginx-delayed service..."
sudo systemctl enable nginx-delayed.service

# Check if Docker is enabled
echo "Ensuring Docker is enabled on boot..."
sudo systemctl enable docker

# Disable regular nginx (we'll use our delayed version)
echo "Disabling regular nginx service (using delayed version)..."
sudo systemctl disable nginx.service || true

# Start the docker service now (if not already running)
echo "Starting docker-apps service..."
sudo systemctl start docker-apps.service

# Wait a bit and then start nginx
echo "Waiting for containers to be ready..."
sleep 45

echo "Starting nginx-delayed service..."
sudo systemctl start nginx-delayed.service

# Check status
echo "Checking service status..."
echo "Docker-apps service:"
sudo systemctl status docker-apps.service --no-pager -l || true

echo ""
echo "Nginx-delayed service:"
sudo systemctl status nginx-delayed.service --no-pager -l || true

echo ""
echo "Container status:"
docker compose ps

echo ""
echo "=== Auto-Start Setup Complete ==="
echo ""
echo "Services configured to start on boot:"
echo "  ✓ docker.service"
echo "  ✓ docker-apps.service (your applications)"
echo "  ✓ nginx-delayed.service (nginx with proper timing)"
echo ""
echo "To manually manage the services:"
echo "  sudo systemctl start docker-apps.service"
echo "  sudo systemctl stop docker-apps.service"
echo "  sudo systemctl restart docker-apps.service"
echo "  sudo systemctl status docker-apps.service"
echo ""
echo "  sudo systemctl start nginx-delayed.service"
echo "  sudo systemctl stop nginx-delayed.service"
echo "  sudo systemctl restart nginx-delayed.service"
echo "  sudo systemctl status nginx-delayed.service"
echo ""
echo "Logs can be viewed with:"
echo "  sudo journalctl -u docker-apps.service -f"
echo "  sudo journalctl -u nginx-delayed.service -f"
echo "  tail -f /var/log/docker-apps-startup.log"
