# Pi Dashboard Troubleshooting and Deployment Guide

## Quick Deployment
Run the complete deployment script:
```bash
./deploy-complete.sh
```

## Manual Deployment Steps

### 1. Deploy to Pi
```bash
# Commit and push changes
git add -A
git commit -m "Deploy: Pi Dashboard $(date '+%Y-%m-%d %H:%M:%S')"
git push

# Copy files to Pi
scp -r . pi@yancmo.xyz:~/pi-dashboard-temp
```

### 2. Setup on Pi
```bash
# SSH into Pi
ssh pi@yancmo.xyz

# Create directory and move files
mkdir -p /home/pi/py-apps
sudo systemctl stop pi-dashboard 2>/dev/null || true
sudo rm -rf /home/pi/py-apps/pi-dashboard
mv ~/pi-dashboard-temp /home/pi/py-apps/pi-dashboard

# Setup Python environment
cd /home/pi/py-apps/pi-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install systemd service
sudo cp systemd/pi-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pi-dashboard

# Setup nginx
sudo cp nginx/dashboard.conf /etc/nginx/sites-available/dashboard
sudo ln -sf /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/
sudo nginx -t

# Start services
sudo systemctl start pi-dashboard
sudo systemctl reload nginx
```

## Troubleshooting Steps

### 1. Check Service Status
```bash
# Check if service is running
sudo systemctl status pi-dashboard

# Check service logs
sudo journalctl -u pi-dashboard -n 50 -f

# Check if port is listening
sudo netstat -tlnp | grep :8080
```

### 2. Check Nginx Configuration
```bash
# Test nginx config
sudo nginx -t

# Check nginx status
sudo systemctl status nginx

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check if dashboard site is enabled
ls -la /etc/nginx/sites-enabled/dashboard
```

### 3. Test Local Connections
```bash
# Test Flask app directly
curl -I http://localhost:8080

# Test nginx proxy
curl -I http://localhost/dashboard/

# Check nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### 4. Common Issues and Solutions

#### Service Won't Start
```bash
# Check Python path and venv
cd /home/pi/py-apps/pi-dashboard
ls -la .venv/bin/python
.venv/bin/python --version

# Check requirements
.venv/bin/pip list

# Test manual start
.venv/bin/python dashboard.py
```

#### 502 Bad Gateway Error
```bash
# Check if Flask app is running
sudo systemctl status pi-dashboard
curl -I http://localhost:8080

# Check nginx upstream
sudo nginx -t
grep -n "proxy_pass" /etc/nginx/sites-available/dashboard
```

#### Permission Issues
```bash
# Check file ownership
ls -la /home/pi/py-apps/pi-dashboard/
sudo chown -R pi:pi /home/pi/py-apps/pi-dashboard/
chmod +x /home/pi/py-apps/pi-dashboard/dashboard.py
```

#### SSL/Domain Issues
```bash
# Check SSL certificate
sudo certbot certificates

# Check DNS resolution
nslookup yancmo.xyz
ping yancmo.xyz

# Test SSL
curl -I https://www.yancmo.xyz/dashboard/
```

### 5. Full System Check Script
```bash
#!/bin/bash
echo "=== Pi Dashboard System Check ==="

echo "1. Service Status:"
sudo systemctl status pi-dashboard --no-pager -l

echo -e "\n2. Port Check:"
sudo netstat -tlnp | grep :8080

echo -e "\n3. Process Check:"
ps aux | grep dashboard

echo -e "\n4. Nginx Status:"
sudo systemctl status nginx --no-pager -l

echo -e "\n5. Nginx Test:"
sudo nginx -t

echo -e "\n6. Local Connection Test:"
curl -I http://localhost:8080

echo -e "\n7. Nginx Proxy Test:"
curl -I http://localhost/dashboard/

echo -e "\n8. Recent Service Logs:"
sudo journalctl -u pi-dashboard -n 10 --no-pager

echo -e "\n9. Recent Nginx Errors:"
sudo tail -n 10 /var/log/nginx/error.log

echo -e "\n10. File Permissions:"
ls -la /home/pi/py-apps/pi-dashboard/dashboard.py
ls -la /home/pi/py-apps/pi-dashboard/.venv/bin/python
```

## Configuration Files

### Nginx Configuration (`/etc/nginx/sites-available/dashboard`)
```nginx
server {
    listen 80;
    server_name yancmo.xyz www.yancmo.xyz;
    
    location /dashboard/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    location /dashboard/static/ {
        alias /home/pi/py-apps/pi-dashboard/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Systemd Service (`/etc/systemd/system/pi-dashboard.service`)
```ini
[Unit]
Description=Pi Dashboard Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/py-apps/pi-dashboard
Environment=PATH=/home/pi/py-apps/pi-dashboard/.venv/bin
ExecStart=/home/pi/py-apps/pi-dashboard/.venv/bin/python dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Testing URLs
- **Local Flask App**: http://localhost:8080
- **Local Nginx Proxy**: http://localhost/dashboard/
- **External HTTPS**: https://www.yancmo.xyz/dashboard/

## Quick Commands Reference
```bash
# Restart dashboard
sudo systemctl restart pi-dashboard

# Reload nginx
sudo systemctl reload nginx

# View logs
sudo journalctl -u pi-dashboard -f

# Test connections
curl -I http://localhost:8080
curl -I https://www.yancmo.xyz/dashboard/
```
