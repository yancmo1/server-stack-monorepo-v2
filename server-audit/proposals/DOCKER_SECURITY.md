# Docker Compose Security Modifications

## Files to Modify

### 1. /opt/apps/docker-compose.yml
Primary application stack - needs localhost binding for all services.

### 2. /home/yancmo/apps/*/docker-compose.yml  
Individual app compose files - check for exposed ports.

## Proposed Changes for /opt/apps/docker-compose.yml

### Current Port Bindings (INSECURE)
```yaml
services:
  dashboard:
    ports:
      - "5550:5550"  # Exposed to 0.0.0.0 (all interfaces)
  cruise:
    ports:
      - "5551:5551"  # Exposed to 0.0.0.0
  clanmap:
    ports:
      - "5552:5552"  # Exposed to 0.0.0.0
  qsl:
    ports:
      - "5553:5553"  # Exposed to 0.0.0.0
  tracker:
    ports:
      - "5554:5554"  # Exposed to 0.0.0.0
  pwa:
    ports:
      - "5555:5555"  # Exposed to 0.0.0.0
  connector:
    ports:
      - "5557:5557"  # Exposed to 0.0.0.0
```

### Secure Port Bindings (LOCALHOST ONLY)
```yaml
services:
  dashboard:
    ports:
      - "127.0.0.1:5550:5550"  # Localhost only
  cruise:
    ports:
      - "127.0.0.1:5551:5551"  # Localhost only
  clanmap:
    ports:
      - "127.0.0.1:5552:5552"  # Localhost only
  qsl:
    ports:
      - "127.0.0.1:5553:5553"  # Localhost only
  tracker:
    ports:
      - "127.0.0.1:5554:5554"  # Localhost only
  pwa:
    ports:
      - "127.0.0.1:5555:5555"  # Localhost only
  connector:
    ports:
      - "127.0.0.1:5557:5557"  # Localhost only
```

## Alternative: Internal Docker Network (Advanced)

### Option A: Custom Bridge Network
```yaml
networks:
  app_network:
    driver: bridge
    internal: false  # Allow outbound internet access
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1

services:
  dashboard:
    networks:
      - app_network
    ports:
      - "127.0.0.1:5550:5550"  # Still bind to localhost for nginx access
```

### Option B: Remove Port Binding Entirely
```yaml
# Remove all port bindings, access only through Docker network
services:
  dashboard:
    # ports: []  # No external ports
    expose:
      - "5550"   # Only expose to other containers
    networks:
      - app_network

  nginx:
    # Add nginx as a container in same network
    ports:
      - "80:80"
      - "443:443"
    networks:
      - app_network
```

## Implementation Commands

### Backup Current Compose File
```bash
sudo cp /opt/apps/docker-compose.yml /opt/apps/docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
```

### Apply Localhost Bindings (Recommended First Step)
```bash
# Edit the compose file with localhost bindings
sudo nano /opt/apps/docker-compose.yml

# Recreate containers with new port bindings
cd /opt/apps
sudo docker-compose down
sudo docker-compose up -d
```

### Verification Commands
```bash
# Check that ports are bound to localhost only
sudo ss -tlnp | grep -E ':(5550|5551|5552|5553|5554|5555|5557)'
# Should show 127.0.0.1:PORT instead of 0.0.0.0:PORT

# Test internal access works
curl -I http://127.0.0.1:5550
curl -I http://localhost:5551

# Test external access blocked (should fail/timeout)
curl -I http://$(curl -s ipinfo.io/ip):5550 --connect-timeout 5
```

## Additional Compose Files to Check

### Files Found in Home Directory
```bash
# Scan for additional docker-compose files
find /home/yancmo -name "docker-compose.yml" -o -name "docker-compose.yaml"
find /opt -name "docker-compose.yml" -o -name "docker-compose.yaml"
```

### Common Patterns to Fix
```yaml
# BEFORE (Insecure)
ports:
  - "8080:8080"        # All interfaces
  - "3000:3000"        # All interfaces
  - "9000:9000"        # All interfaces

# AFTER (Secure)  
ports:
  - "127.0.0.1:8080:8080"  # Localhost only
  - "127.0.0.1:3000:3000"  # Localhost only
  - "127.0.0.1:9000:9000"  # Localhost only
```

## Testing Strategy

### Phase 1: Localhost Binding Test
1. Update ONE service first (e.g., dashboard)
2. Test access via localhost:5550 
3. Verify external access blocked
4. Test nginx proxy to localhost:5550
5. Apply to remaining services

### Phase 2: Full Stack Validation
1. Apply all localhost bindings
2. Deploy nginx subdomain configs
3. Test each subdomain endpoint
4. Update DNS records for subdomains
5. Apply UFW firewall restrictions

## Rollback Procedure
```bash
# Quick rollback to original configuration
cd /opt/apps
sudo docker-compose down
sudo cp docker-compose.yml.backup.[timestamp] docker-compose.yml
sudo docker-compose up -d

# Verify original state restored
sudo ss -tlnp | grep -E ':(5550|5551|5552|5553|5554|5555|5557)'
```