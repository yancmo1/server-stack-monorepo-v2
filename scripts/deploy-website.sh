#!/bin/bash
# Website deployment script for Ubuntu server

echo "🚀 Deploying Yancmo.xyz website with Pi-hole proxy..."

# Create web directory
echo "📁 Creating web directory..."
sudo mkdir -p /var/www/yancmo.xyz
sudo chown yancmo:yancmo /var/www/yancmo.xyz

# Copy website files
echo "📄 Copying website files..."
sudo cp /home/yancmo/index.html /var/www/yancmo.xyz/
sudo chown yancmo:yancmo /var/www/yancmo.xyz/index.html

# Backup existing nginx config
echo "💾 Backing up existing nginx config..."
sudo cp /etc/nginx/sites-available/yancmo.xyz /etc/nginx/sites-available/yancmo.xyz.backup.$(date +%Y%m%d-%H%M%S) 2>/dev/null || true

# Install new nginx config
echo "⚙️ Installing new nginx configuration..."
sudo cp /home/yancmo/yancmo.xyz.conf /etc/nginx/sites-available/yancmo.xyz

# Enable the site
echo "🔗 Enabling site..."
sudo ln -sf /etc/nginx/sites-available/yancmo.xyz /etc/nginx/sites-enabled/

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid!"
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    echo "✅ Website deployment completed!"
    echo ""
    echo "🌐 Your website should now be accessible at:"
    echo "   • https://yancmo.xyz/"
    echo "   • https://yancmo.xyz/pihole/ (Pi-hole admin)"
    echo "   • https://yancmo.xyz/cruise/ (Cruise monitor)"
    echo "   • https://yancmo.xyz/qsl/ (QSL creator)"
else
    echo "❌ Nginx configuration test failed!"
    echo "Please check the configuration and try again."
    exit 1
fi
