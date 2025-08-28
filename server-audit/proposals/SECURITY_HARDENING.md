# UFW Firewall Hardening Plan

## Current State Analysis
Based on the server audit, the following ports are currently exposed publicly:
- **HIGH RISK**: Ports 5550-5557 (Docker apps) - Direct container access
- **MEDIUM RISK**: Port 9090 (Prometheus) - Metrics server with admin capabilities
- **MEDIUM RISK**: Port 8888 (Unknown service) - Needs investigation
- **ACCEPTABLE**: Ports 22, 80, 443 (SSH, HTTP, HTTPS) - Standard web services

## Proposed UFW Rule Changes

### Phase 1: Remove Public Access to High-Risk Ports
```bash
# Remove public access to Docker app ports
sudo ufw delete allow 5550
sudo ufw delete allow 5551  
sudo ufw delete allow 5552
sudo ufw delete allow 5553
sudo ufw delete allow 5554
sudo ufw delete allow 5555
sudo ufw delete allow 5557

# Remove public access to Prometheus
sudo ufw delete allow 9090

# Remove public access to unknown service (investigate first)
sudo ufw delete allow 8888
```

### Phase 2: Restrict Admin Services to Tailscale Network
```bash
# Allow Prometheus only from Tailscale network (100.64.0.0/10)
sudo ufw allow from 100.64.0.0/10 to any port 9090 comment 'Prometheus Tailscale only'

# Allow Grafana only from Tailscale network (if not behind reverse proxy)
sudo ufw allow from 100.64.0.0/10 to any port 3000 comment 'Grafana Tailscale only'

# Allow Syncthing only from Tailscale network
sudo ufw allow from 100.64.0.0/10 to any port 8384 comment 'Syncthing WebUI Tailscale only'
sudo ufw allow from 100.64.0.0/10 to any port 22000 comment 'Syncthing Sync Tailscale only'

# Allow Pi-hole admin only from Tailscale network (if separate admin port)
sudo ufw allow from 100.64.0.0/10 to any port 4711 comment 'Pi-hole admin Tailscale only'
```

### Phase 3: Verify Current Rules and Clean Up
```bash
# Show current rules
sudo ufw status numbered

# Remove any duplicate or conflicting rules
# (Commands will be generated after seeing current state)

# Reload firewall
sudo ufw reload
```

## Docker Network Security Modifications

### Current Issues in docker-compose.yml
```yaml
# PROBLEM: Binds to all interfaces (0.0.0.0)
ports:
  - "5550:5550"  # dashboard
  - "5551:5551"  # cruise
  - "5552:5552"  # clanmap
  - "5553:5553"  # qsl
  - "5554:5554"  # tracker
  - "5555:5555"  # pwa
  - "5557:5557"  # connector
```

### Proposed Secure Port Binding
```yaml
# SOLUTION: Bind only to localhost
ports:
  - "127.0.0.1:5550:5550"  # dashboard - localhost only
  - "127.0.0.1:5551:5551"  # cruise - localhost only
  - "127.0.0.1:5552:5552"  # clanmap - localhost only
  - "127.0.0.1:5553:5553"  # qsl - localhost only
  - "127.0.0.1:5554:5554"  # tracker - localhost only
  - "127.0.0.1:5555:5555"  # pwa - localhost only
  - "127.0.0.1:5557:5557"  # connector - localhost only
```

## Implementation Timeline

### Immediate Actions (Safe to execute now)
1. ✅ **Backup running** - MEGA backup in progress
2. ✅ **Nginx configs created** - Reverse proxy configurations ready
3. 🔄 **Test Nginx configs** - Validate configurations before deployment

### Next Phase (Requires coordination)
1. **Install SSL certificates** - Run certbot for all subdomains
2. **Deploy Nginx configs** - Copy server blocks to sites-available/enabled
3. **Update Docker compose** - Change port bindings to localhost
4. **Update UFW rules** - Remove public access to high ports
5. **Test all services** - Verify functionality through subdomains

### Verification Commands
```bash
# Test that services are only accessible via localhost
curl -I http://localhost:5550  # Should work
curl -I http://public_ip:5550  # Should fail after changes

# Test subdomain access
curl -I https://dashboard.yancmo.xyz  # Should work after deployment

# Verify firewall rules
sudo ufw status numbered
sudo ss -tlnp | grep -E ':(5550|5551|5552|5553|5554|5555|5557|9090)'
```

## Rollback Plan
If issues occur:
1. **UFW rollback**: `sudo ufw reset` (restores default rules)
2. **Docker rollback**: Revert port bindings to original state
3. **Nginx rollback**: Disable site configs, restart nginx
4. **DNS rollback**: Remove subdomain DNS entries if needed

## Security Benefits
- ✅ **Eliminates direct container access** from internet
- ✅ **Centralizes SSL termination** at Nginx layer
- ✅ **Enables rate limiting** and access controls
- ✅ **Reduces attack surface** by 7 exposed ports
- ✅ **Enables monitoring** of all web traffic through single point
- ✅ **Supports IP restriction** for admin interfaces