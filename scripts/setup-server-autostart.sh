#!/bin/bash
# Remote setup script for auto-start configuration

echo "=== Setting up Auto-Start Services on Server ==="

# Connect to server and run setup
ssh yancmo@ubuntumac << 'EOF'
    cd ~/apps/server-stack-monorepo-v2
    
    echo "--- Pulling latest changes ---"
    git pull
    
    echo "--- Setting up auto-start configuration ---"
    cd deploy
    
    # Run the setup script
    bash setup-autostart.sh
    
    echo "--- Verifying services ---"
    echo "Docker service status:"
    sudo systemctl status docker --no-pager -l
    
    echo ""
    echo "Docker-apps service status:"
    sudo systemctl status docker-apps --no-pager -l
    
    echo ""
    echo "Nginx service status:"
    sudo systemctl status nginx --no-pager -l
    
    echo ""
    echo "Current container status:"
    docker compose ps
    
    echo ""
    echo "=== Setup Complete ==="
EOF
