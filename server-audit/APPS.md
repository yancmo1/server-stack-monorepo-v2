# Apps and Services Inventory (draft)

This is a living inventory. Update as apps change.

| App/Service        | Type          | Unit/Container              | Ports (host)            | Exposure          | URL (placeholder)             | Notes |
|--------------------|---------------|-----------------------------|-------------------------|-------------------|-------------------------------|-------|
| Nginx              | reverse-proxy | systemd: nginx.service      | 80/tcp, 443/tcp         | Public            | https://<domain>              | Conflicting server_name warnings; dedupe vhosts. |
| Prometheus         | monitoring    | systemd: prometheus.service | 9090/tcp                | Public (UFW allow)| https://metrics.<domain>      | Restrict to your IP/Tailscale or behind RP. |
| Grafana            | monitoring    | systemd: grafana-server.service | 3000/tcp           | Listening (*:3000)| https://grafana.<domain>      | Bind to 127.0.0.1 and proxy via Nginx. |
| Pi-hole FTL        | DNS           | systemd: pihole-FTL.service | 53/tcp,53/udp          | LAN/Tailscale     | n/a                           | Ensure DNS only allowed from LAN/Tailscale. |
| Tinyproxy          | proxy         | systemd: tinyproxy.service  | 8888/tcp               | Public (UFW allow)| n/a                           | High risk if public; restrict to IP/Tailscale. |
| Syncthing          | sync          | process: syncthing          | 8384/tcp, 22000 tcp/udp| Tailscale only    | https://syncthing.<domain>    | 8384 allowed on tailscale0; OK. |
| coc-discord-bot    | app           | docker: deploy-coc-discord-bot-1 | (none)           | n/a              | n/a                           | No host ports; good. |
| dashboard          | app           | docker: dashboard           | 5550/tcp               | Public (Docker)   | https://dashboard.<domain>    | Rebind to 127.0.0.1 and proxy via Nginx. |
| cruise-price-check | app           | docker: cruise-price-check  | 5551/tcp               | Public (Docker)   | https://cruise.<domain>       | Rebind to 127.0.0.1 and proxy via Nginx. |
| clan-map           | app           | docker: clan-map            | 5552/tcp               | Public (Docker)   | https://clanmap.<domain>      | Rebind to 127.0.0.1 and proxy via Nginx. |
| qsl-card-creator   | app           | docker: qsl-card-creator    | 5553/tcp               | Public (Docker)   | https://qsl.<domain>          | Rebind to 127.0.0.1 and proxy via Nginx. |
| tracker            | app           | docker: tracker             | 5554/tcp               | Public (Docker)   | https://tracker.<domain>      | Rebind to 127.0.0.1 and proxy via Nginx. |
| pwa-tracker        | app           | docker: pwa-tracker         | 5555/tcp               | Public (Docker)   | https://pwa.<domain>          | Rebind to 127.0.0.1 and proxy via Nginx. |
| qsl-connector      | app           | docker: qsl-connector       | 5557/tcp               | Public (Docker)   | n/a (internal)                 | Consider internal-only network exposure. |
| Postgres (system)  | database      | systemd: postgresql@16-main | 5432/tcp (127.0.0.1)   | Localhost only    | n/a                           | Good. |
| cocstack-db        | database      | docker: cocstack-db         | (container only)       | Internal          | n/a                           | Dump via docker exec. |
| tracker-db         | database      | docker: tracker-db          | (container only)       | Internal          | n/a                           | Dump via docker exec. |

> Replace <domain> placeholders with your actual subdomains once routing is finalized.
