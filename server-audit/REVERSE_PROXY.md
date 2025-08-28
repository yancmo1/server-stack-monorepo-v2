# Reverse Proxy and Routing Plan

Objective
- One front door on :80/:443 (Nginx currently installed) serving all apps via subdomains.
- Backends bind to localhost or Docker networks (no direct 0.0.0.0 exposure).
- Strong TLS and security headers; support WebSocket upgrades.

Recommended subdomain map (example)
- dashboard.<domain> → localhost:5550 (Docker app)
- cruise.<domain> → localhost:5551
- clanmap.<domain> → localhost:5552
- qsl.<domain> → localhost:5553
- tracker.<domain> → localhost:5554
- pwa.<domain> → localhost:5555
- grafana.<domain> → localhost:3000 (bind Grafana to 127.0.0.1)
- prometheus.<domain> (optional, or restrict to Tailscale only)
- syncthing.<domain> (optional admin UI; restrict by IP or auth)

Nginx server block template

server {
    listen 80;
    listen [::]:80;
    server_name app.<domain>;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name app.<domain>;

    # TLS certs (managed by certbot or your choice)
    ssl_certificate     /etc/letsencrypt/live/app.<domain>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.<domain>/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy no-referrer-when-downgrade always;

    location / {
        proxy_pass http://127.0.0.1:PORT;  # replace PORT per app
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}

Docker-friendly option
- Place each app on a user-defined Docker bridge network.
- Use proxy_pass http://container_name:PORT; and enable resolver 127.0.0.11 ipv6=off; inside Nginx container, or run Nginx on the host with `--net=host` and add /etc/hosts entries if needed.

Traefik alternative (labels example)

labels:
  - "traefik.enable=true"
  - "traefik.http.routers.app.rule=Host(`app.<domain>`)"
  - "traefik.http.routers.app.entrypoints=websecure"
  - "traefik.http.routers.app.tls.certresolver=letsencrypt"
  - "traefik.http.services.app.loadbalancer.server.port=PORT"

Notes
- Fix duplicated/conflicting Nginx server_name entries for your apex/www vhosts.
- Prefer per-app files in /etc/nginx/sites-available with symlinks in sites-enabled.
- Test: nginx -t (read-only check). Reload only after you approve.
