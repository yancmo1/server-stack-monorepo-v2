# Firewall Plan (UFW + Docker + Tailscale)

Goals
- Keep default deny inbound; allow only necessary ports to the public.
- Prefer Tailscale or IP allowlists for admin/monitoring surfaces.
- Ensure Docker-exposed ports are not publicly reachable unless intended.

Current highlights (from audit)
- UFW: default deny; public allows for 22/tcp, 80/tcp, 443/tcp, 9090, 8888; tailscale0 allows for 8080/8443/22000/8384.
- Docker publishes many app ports on 0.0.0.0:5550–5557.

Recommendations
1) Close public access to admin/monitoring ports:
   - Restrict 9090 (Prometheus) to your IP(s) or Tailscale only, or remove allow rule and route via reverse proxy with auth.
   - Restrict 8888 (Tinyproxy) or disable if not needed; otherwise limit to your IP/Tailscale.
2) Move app ports behind reverse proxy:
   - Change containers to bind 127.0.0.1:PORT or internal-only and remove public exposure; access via Nginx.
3) SSH hardening:
   - Keep 22/tcp open; optionally restrict by IP/Tailscale. Large GitHub Actions IP ranges are allowed currently—review if still needed.
4) Confirm DNS (53) exposure:
   - Ensure Pi-hole only serves LAN/Tailscale; avoid public internet exposure.

Example UFW rule set (concept)
- Allow 22/tcp, 80/tcp, 443/tcp Anywhere
- Deny/Remove public 9090 and 8888; re-add allows on tailscale0 or specific CIDRs
- No public allows for 5550–5557 once behind RP

Docker notes
- Consider `--publish 127.0.0.1:PORT:PORT` to limit exposure
- Or use a user-defined bridge network and Nginx to reach containers by name
