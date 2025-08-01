# 5K Tracker PWA - HTTPS Setup and Deployment Guide

## Overview

The 5K Tracker has been converted to a Progressive Web App (PWA). PWAs require HTTPS to function properly, especially for service worker registration and installation features.

## Local Development with HTTPS

### Option 1: Using mkcert (Recommended)

1. **Install mkcert:**
   ```bash
   # On macOS with Homebrew
   brew install mkcert
   
   # On Ubuntu/Debian
   curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
   chmod +x mkcert-v*-linux-amd64
   sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
   
   # On Windows with Chocolatey
   choco install mkcert
   ```

2. **Create local CA:**
   ```bash
   mkcert -install
   ```

3. **Generate certificates for localhost:**
   ```bash
   cd /path/to/5k-tracker
   mkcert localhost 127.0.0.1 ::1
   ```

4. **Update your Flask development server:**
   Create a `run_https.py` file:
   ```python
   from app import app
   
   if __name__ == '__main__':
       app.run(
           host='localhost',
           port=5001,
           ssl_context=('localhost+2.pem', 'localhost+2-key.pem'),
           debug=True
       )
   ```

5. **Run with HTTPS:**
   ```bash
   python run_https.py
   ```

### Option 2: Using Self-Signed Certificates

1. **Generate self-signed certificate:**
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
   ```

2. **Run Flask with SSL:**
   ```python
   from app import app
   
   if __name__ == '__main__':
       app.run(
           host='localhost',
           port=5001,
           ssl_context=('cert.pem', 'key.pem'),
           debug=True
       )
   ```

**Note:** Self-signed certificates will show security warnings in browsers, but PWA features will still work for testing.

## Production Deployment

### Prerequisites for PWA Functionality

1. **HTTPS is mandatory** - PWAs will not install or function properly over HTTP
2. **Valid SSL certificate** - Use Let's Encrypt, CloudFlare, or a commercial CA
3. **Proper domain/subdomain** - localhost and IP addresses have limited PWA support

### Deployment Options

#### Option 1: Nginx + Gunicorn with Let's Encrypt

1. **Install Certbot:**
   ```bash
   sudo apt update
   sudo apt install certbot python3-certbot-nginx
   ```

2. **Obtain SSL certificate:**
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Nginx configuration:**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       location /tracker/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_set_header X-Script-Name /tracker;
       }
   }
   
   # Redirect HTTP to HTTPS
   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }
   ```

4. **Run Gunicorn:**
   ```bash
   gunicorn -w 4 -b 127.0.0.1:8000 app:app
   ```

#### Option 2: Docker with Traefik (Automatic HTTPS)

1. **Update docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     traefik:
       image: traefik:v2.9
       command:
         - --api.dashboard=true
         - --entrypoints.web.address=:80
         - --entrypoints.websecure.address=:443
         - --providers.docker=true
         - --certificatesresolvers.letsencrypt.acme.email=your-email@domain.com
         - --certificatesresolvers.letsencrypt.acme.storage=/acme.json
         - --certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock
         - ./acme.json:/acme.json
       labels:
         - traefik.http.routers.api.rule=Host(`traefik.yourdomain.com`)
         - traefik.http.routers.api.service=api@internal
         - traefik.http.routers.api.tls.certresolver=letsencrypt
   
     5k-tracker:
       build: .
       labels:
         - traefik.enable=true
         - traefik.http.routers.tracker.rule=Host(`yourdomain.com`) && PathPrefix(`/tracker`)
         - traefik.http.routers.tracker.tls.certresolver=letsencrypt
         - traefik.http.services.tracker.loadbalancer.server.port=8000
   ```

#### Option 3: CloudFlare with Flexible SSL

1. **Set up CloudFlare:**
   - Add your domain to CloudFlare
   - Set SSL/TLS mode to "Flexible" or "Full"
   - Enable "Always Use HTTPS"

2. **Deploy to any hosting provider:**
   - Heroku, DigitalOcean, AWS, etc.
   - CloudFlare handles HTTPS termination

### Environment Variables

Set these environment variables for production:

```bash
export FLASK_ENV=production
export TRACKER_SECRET_KEY=your-secret-key-here
export TRACKER_DATABASE_URI=your-database-url
```

## Testing PWA Functionality

### Desktop Testing

1. **Chrome/Edge:**
   - Open Developer Tools
   - Go to Application tab → Service Workers
   - Check for registration
   - Look for install prompt in address bar

2. **Firefox:**
   - Open Developer Tools
   - Go to Application tab → Service Workers
   - Test offline functionality

### Mobile Testing

1. **Android Chrome:**
   - Visit your HTTPS site
   - Look for "Add to Home Screen" prompt
   - Install and test standalone mode

2. **iOS Safari:**
   - Visit your HTTPS site
   - Tap Share button → "Add to Home Screen"
   - Test standalone functionality

### PWA Testing Checklist

- [ ] HTTPS is working correctly
- [ ] Manifest.json is accessible and valid
- [ ] Service worker registers successfully
- [ ] Icons display correctly in various sizes
- [ ] Install prompt appears on supported browsers
- [ ] App works in standalone mode
- [ ] Offline functionality works
- [ ] Network status indicator functions
- [ ] App shortcuts work (if supported)

## Troubleshooting

### Service Worker Issues

1. **Clear browser cache and data**
2. **Check browser console for errors**
3. **Verify service worker scope matches app routes**
4. **Ensure HTTPS is properly configured**

### Installation Issues

1. **Verify manifest.json syntax**
2. **Check icon file paths and sizes**
3. **Ensure start_url is accessible**
4. **Test on different devices/browsers**

### SSL Certificate Issues

1. **Verify certificate chain is complete**
2. **Check certificate expiration**
3. **Test with SSL testing tools (ssllabs.com)**
4. **Ensure proper redirects from HTTP to HTTPS**

## Monitoring and Maintenance

1. **Set up SSL certificate auto-renewal**
2. **Monitor service worker updates**
3. **Track PWA installation analytics**
4. **Keep dependencies updated**
5. **Test on new browser versions**

## Security Considerations

1. **Use strong SSL/TLS configuration**
2. **Implement Content Security Policy (CSP)**
3. **Keep service worker cache updated**
4. **Monitor for security vulnerabilities**
5. **Use HTTPS for all external resources**