     #!/bin/bash
     # Server Audit Script - Run this on your Ubuntu server
     # This will help us understand your current setup

     echo "=== SERVER AUDIT REPORT ==="
     echo "Date: $(date)"
     echo "Host: $(hostname)"
     echo "User: $(whoami)"
     echo ""

     echo "=== SYSTEM INFO ==="
     uname -a
     echo ""

     echo "=== RUNNING PROCESSES (Python/Bot related) ==="
     ps aux | grep -E "(python|bot|discord|coc)" | grep -v grep
     echo ""

     echo "=== ACTIVE SERVICES ==="
     systemctl list-units --type=service --state=running | grep -E
     "(bot|discord|coc|web|nginx|apache)"
     echo ""

     echo "=== NETWORK SERVICES ==="
     ss -tlnp | grep -E "(80|443|3000|5000|8000|8080)"
     echo ""

     echo "=== DOCKER STATUS ==="
     docker --version 2>/dev/null || echo "Docker not installed/running"
     docker ps -a 2>/dev/null || echo "No Docker containers or permission 
     denied"
     echo ""

     echo "=== USER DIRECTORIES ==="
     echo "Home directory contents:"
     ls -la ~/
     echo ""

     echo "Apps directory (if exists):"
     ls -la ~/apps/ 2>/dev/null || echo "No ~/apps directory"
     echo ""

     echo "=== PYTHON ENVIRONMENTS ==="
     which python3
     python3 --version
     echo ""
     echo "Virtual environments:"
     find ~ -name ".venv" -type d 2>/dev/null | head -10
     find ~ -name "venv" -type d 2>/dev/null | head -10
     echo ""

     echo "=== WEB SERVER CHECK ==="
     curl -I http://localhost:80 2>/dev/null || echo "No web server on 
     port 80"
     curl -I http://localhost:8000 2>/dev/null || echo "No web server on 
     port 8000"
     curl -I http://localhost:3000 2>/dev/null || echo "No web server on 
     port 3000"
     echo ""

     echo "=== DISCORD BOT SEARCH ==="
     find ~ -name "*bot*" -type d 2>/dev/null | head -10
     find ~ -name "*discord*" -type d 2>/dev/null | head -10
     find ~ -name "*coc*" -type d 2>/dev/null | head -10
     echo ""

     echo "=== RECENT LOG FILES ==="
     find ~ -name "*.log" -mtime -7 2>/dev/null | head -10
     echo ""

     echo "=== CRON JOBS ==="
     crontab -l 2>/dev/null || echo "No user crontab"
     echo ""

     echo "=== SYSTEMD USER SERVICES ==="
     systemctl --user list-units --type=service 2>/dev/null | head -20 ||
     echo "No user services or systemd user not enabled"
     echo ""

     echo "=== AUDIT COMPLETE ==="
