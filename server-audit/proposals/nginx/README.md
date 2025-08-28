# Nginx Subdomain Reverse Proxy Configuration

This directory contains proposed Nginx server block configurations to route subdomains to your Docker apps. These configs will replace the current port-based access with clean subdomain routing.

## Proposed subdomain mapping
- dashboard.yancmo.xyz → localhost:5550 (dashboard)
- cruise.yancmo.xyz → localhost:5551 (cruise-price-check)
- clanmap.yancmo.xyz → localhost:5552 (clan-map)
- qsl.yancmo.xyz → localhost:5553 (qsl-card-creator)
- tracker.yancmo.xyz → localhost:5554 (tracker)
- pwa.yancmo.xyz → localhost:5555 (pwa-tracker)
- connector.yancmo.xyz → localhost:5557 (qsl-connector)
- grafana.yancmo.xyz → localhost:3000 (grafana)
- metrics.yancmo.xyz → localhost:9090 (prometheus, with IP restriction)
- syncthing.yancmo.xyz → localhost:8384 (syncthing UI, with IP/auth restriction)

## Installation plan (after approval)
1. Copy these server block files to `/etc/nginx/sites-available/`
2. Create symlinks in `/etc/nginx/sites-enabled/`
3. Test with `nginx -t`
4. Obtain SSL certificates via certbot (automated)
5. Reload nginx
6. Update Docker compose files to bind to localhost only
7. Update UFW to remove public high port access

## Security features included
- HTTP → HTTPS redirect
- Strong SSL configuration
- Security headers (HSTS, X-Frame-Options, etc.)
- WebSocket support for apps that need it
- Rate limiting for public endpoints
- IP-based restrictions for admin interfaces

Replace `yancmo.xyz` with your actual domain in all files.