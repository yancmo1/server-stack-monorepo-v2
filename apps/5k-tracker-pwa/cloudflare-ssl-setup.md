# Using Existing Cloudflare Certificates

## Your Setup
- **Certificates Location**: `/etc/ssl/cloudflare/`
- **Public Domain**: `www.yancmo.xyz`
- **App**: Race Tracker on port 5011

## Step 1: Check  Your Certificate Files
```bash
# On your Pi, check what cert files you have
ls -la /etc/ssl/cloudflare/
```

Common filenames might be:
- `yancmo.xyz.crt` or `www.yancmo.xyz.crt`
- `yancmo.xyz.key` or `www.yancmo.xyz.key`

## Step 2: Update Nginx Configuration

```bash
# Backup current config
sudo cp /etc/nginx/sites-available/yancmo-main /etc/nginx/sites-available/yancmo-main.backup

# Edit the config
sudo nano /etc/nginx/sites-available/yancmo-main
```

Update the SSL certificate lines to use your existing Cloudflare certificates:

```nginx
server {
    listen 443 ssl http2;
    server_name www.yancmo.xyz yancmo.xyz;
    
    # Use your existing Cloudflare certificates
    ssl_certificate /etc/ssl/cloudflare/yancmo.xyz.crt;
    ssl_certificate_key /etc/ssl/cloudflare/yancmo.xyz.key;
    
    # Race Tracker App
    location /race-tracker/ {
        proxy_pass http://127.0.0.1:5011/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Your other locations...
}
```

## Step 3: Test and Reload

```bash
# Test nginx configuration
sudo nginx -t

# If successful, reload nginx
sudo systemctl reload nginx
```

## Step 4: Set Cloudflare SSL Mode

In Cloudflare Dashboard:
- Go to SSL/TLS → Overview  
- Set encryption mode to **"Full (strict)"**

## Your Race Tracker will be available at:
- **https://www.yancmo.xyz/race-tracker/**

This provides end-to-end encryption: Users → Cloudflare → Your Pi
