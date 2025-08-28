#!/bin/bash
# Dashboard Troubleshooting Script
# Run this on your Pi to diagnose dashboard issues

echo "🔍 Pi Dashboard Troubleshooting"
echo "================================"

# Check if dashboard service exists and is running
echo "📊 Service Status:"
if systemctl list-units --all | grep -q pi-dashboard; then
    sudo systemctl status pi-dashboard --no-pager
else
    echo "❌ pi-dashboard service not found"
fi
echo ""

# Check if Flask app is listening on port 8080
echo "🌐 Port 8080 Status:"
if netstat -tlnp 2>/dev/null | grep -q :8080; then
    echo "✅ Something is listening on port 8080"
    netstat -tlnp 2>/dev/null | grep :8080
else
    echo "❌ Nothing listening on port 8080"
fi
echo ""

# Check if dashboard directory exists
echo "📁 Dashboard Directory:"
if [ -d "/home/pi/py-apps/pi-dashboard" ]; then
    echo "✅ Dashboard directory exists"
    ls -la /home/pi/py-apps/pi-dashboard/
else
    echo "❌ Dashboard directory not found"
fi
echo ""

# Check nginx configuration
echo "🌍 Nginx Configuration:"
if nginx -t 2>/dev/null; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors:"
    nginx -t
fi
echo ""

# Check if dashboard config is included
echo "📋 Dashboard Config Check:"
if [ -f "/etc/nginx/sites-available/dashboard" ]; then
    echo "✅ Dashboard config exists"
else
    echo "❌ Dashboard config not found at /etc/nginx/sites-available/dashboard"
fi

if [ -f "/etc/nginx/sites-enabled/dashboard" ]; then
    echo "✅ Dashboard config is enabled"
else
    echo "❌ Dashboard config not enabled"
fi
echo ""

# Test local connection to Flask app
echo "🔌 Local Connection Test:"
if curl -s http://localhost:8080 >/dev/null; then
    echo "✅ Flask app responds on localhost:8080"
else
    echo "❌ Flask app not responding on localhost:8080"
fi
echo ""

# Check recent logs
echo "📝 Recent Service Logs:"
sudo journalctl -u pi-dashboard --no-pager -n 10
echo ""

echo "🔧 Common Fixes:"
echo "1. Restart dashboard: sudo systemctl restart pi-dashboard"
echo "2. Restart nginx: sudo systemctl restart nginx"
echo "3. Check dashboard logs: sudo journalctl -u pi-dashboard -f"
echo "4. Check nginx logs: sudo tail -f /var/log/nginx/error.log"
echo "5. Test direct access: curl http://localhost:8080"
