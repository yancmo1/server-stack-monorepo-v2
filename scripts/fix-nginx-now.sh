#!/bin/bash
# Quick fix script to start nginx after containers are up

echo "=== Manually starting nginx ==="

ssh yancmo@ubuntumac << 'EOF'
    echo "Waiting for containers to stabilize..."
    sleep 10
    
    echo "Starting nginx..."
    sudo systemctl start nginx
    
    echo "Checking nginx status:"
    sudo systemctl status nginx --no-pager -l || true
    
    echo ""
    echo "Checking websites:"
    curl -k -s -o /dev/null -w "%{http_code}" https://track.yancmo.xyz || echo "Tracker check failed"
    echo " - Tracker status"
    
    curl -k -s -o /dev/null -w "%{http_code}" https://yancmo.xyz || echo "Main site check failed"  
    echo " - Main site status"
EOF
