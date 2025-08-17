#!/bin/bash
# SSL and Site Verification Script

echo "=== SSL and Site Verification ==="
echo ""

# Check nginx status
echo "1. Checking nginx status..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx is not running"
    echo "   Run: sudo systemctl start nginx"
fi

# Check race tracker service
echo ""
echo "2. Checking race-tracker service..."
if systemctl is-active --quiet race-tracker; then
    echo "✅ Race Tracker service is running"
else
    echo "❌ Race Tracker service is not running"
    echo "   Run: sudo systemctl start race-tracker"
fi

# Check if port 5011 is listening
echo ""
echo "3. Checking if Flask app is listening on port 5011..."
if netstat -tuln | grep -q ":5011 "; then
    echo "✅ Flask app is listening on port 5011"
else
    echo "❌ Nothing listening on port 5011"
    echo "   Check race-tracker service logs: sudo journalctl -u race-tracker -f"
fi

# Check SSL certificate
echo ""
echo "4. Checking SSL certificate..."
if [ -f "/etc/ssl/cloudflare/yancmo.xyz.crt" ] && [ -f "/etc/ssl/cloudflare/yancmo.xyz.key" ]; then
    echo "✅ SSL certificates found in /etc/ssl/cloudflare/"
    ls -la /etc/ssl/cloudflare/
else
    echo "❌ SSL certificates not found in /etc/ssl/cloudflare/"
    echo "   Expected: yancmo.xyz.crt and yancmo.xyz.key"
fi

# Test local connections
echo ""
echo "5. Testing local connections..."

# Test HTTP redirect
echo -n "   HTTP redirect (port 80): "
if timeout 5 curl -s -I http://localhost 2>/dev/null | grep -q "301\|302"; then
    echo "✅ Working"
else
    echo "❌ Not working"
fi

# Test HTTPS
echo -n "   HTTPS (port 443): "
if timeout 5 curl -s -k -I https://localhost 2>/dev/null | grep -q "200\|301\|302"; then
    echo "✅ Working"
else
    echo "❌ Not working"
fi

# Test race tracker specifically
echo -n "   Race Tracker app: "
if timeout 5 curl -s http://127.0.0.1:5011 2>/dev/null | grep -q "html\|<!DOCTYPE\|<title"; then
    echo "✅ Working"
else
    echo "❌ Not responding"
fi

# Check firewall
echo ""
echo "6. Checking firewall status..."
if command -v ufw >/dev/null 2>&1; then
    if ufw status | grep -q "Status: active"; then
        echo "✅ UFW firewall is active"
        echo "   Open ports:"
        ufw status | grep ALLOW
    else
        echo "⚠️  UFW firewall is inactive"
    fi
else
    echo "⚠️  UFW not installed"
fi

# Test external connectivity
echo ""
echo "7. Testing external connectivity..."

# Check if we can resolve the domain
echo -n "   DNS resolution: "
if nslookup www.yancmo.xyz 8.8.8.8 >/dev/null 2>&1; then
    echo "✅ Domain resolves"
else
    echo "❌ Domain not resolving"
    echo "      Check Cloudflare DNS settings"
fi

# Final summary
echo ""
echo "=== Summary ==="
echo "If all checks above are ✅, your site should be working at:"
echo "🔗 https://www.yancmo.xyz/race-tracker/"
echo ""
echo "If you see ❌ errors, address them in order:"
echo "1. Fix nginx and race-tracker services first"
echo "2. Check SSL certificates"
echo "3. Verify firewall allows traffic"
echo "4. Check DNS and Cloudflare settings"
echo ""
echo "For detailed logs:"
echo "• Nginx: sudo tail -f /var/log/nginx/error.log"
echo "• Race Tracker: sudo journalctl -u race-tracker -f"
echo "• System: sudo journalctl -xe"
