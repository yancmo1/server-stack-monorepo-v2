#!/bin/bash
# Quick homepage update - just run this on your Pi

sudo sed -i '/location = \//,/add_header Content-Type text\/html;/c\
    # Root location - minimal placeholder\
    location = / {\
        return 200 '\''<h1 style="font-family:sans-serif;text-align:center;margin-top:40vh;color:#333">yancmo.xyz</h1>'\'';\
        add_header Content-Type text/html;\
    }' /etc/nginx/sites-available/yancmo-main

# Test and reload nginx
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Homepage updated to minimal placeholder"
echo "🌐 Visit: https://www.yancmo.xyz/"
