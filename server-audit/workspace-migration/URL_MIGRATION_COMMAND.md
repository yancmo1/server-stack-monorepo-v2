# URL Migration Command for Other Workspaces

## Quick Command to Paste in Other Workspace Chat:

```
Please help me migrate all URL references from port-based to subdomain-based URLs. Here's the mapping:

OLD PORT-BASED URLs → NEW SUBDOMAIN URLs:
- http://yancmo.xyz:5550 → https://dashboard.yancmo.xyz
- https://yancmo.xyz:5550 → https://dashboard.yancmo.xyz
- http://136.228.117.217:5550 → https://dashboard.yancmo.xyz

- http://yancmo.xyz:5551 → https://cruise.yancmo.xyz
- https://yancmo.xyz:5551 → https://cruise.yancmo.xyz
- http://136.228.117.217:5551 → https://cruise.yancmo.xyz

- http://yancmo.xyz:5552 → https://clashmap.yancmo.xyz
- https://yancmo.xyz:5552 → https://clashmap.yancmo.xyz
- http://136.228.117.217:5552 → https://clashmap.yancmo.xyz
- Any references to "clanmap" → "clashmap"

- http://yancmo.xyz:5553 → https://qsl.yancmo.xyz
- https://yancmo.xyz:5553 → https://qsl.yancmo.xyz
- http://136.228.117.217:5553 → https://qsl.yancmo.xyz

- http://yancmo.xyz:5554 → https://crumb.yancmo.xyz
- https://yancmo.xyz:5554 → https://crumb.yancmo.xyz
- http://136.228.117.217:5554 → https://crumb.yancmo.xyz

- http://yancmo.xyz:5555 → https://tracker.yancmo.xyz
- https://yancmo.xyz:5555 → https://tracker.yancmo.xyz
- http://136.228.117.217:5555 → https://tracker.yancmo.xyz
- Any references to "pwa" → "tracker"

- http://yancmo.xyz:5557 → https://connector.yancmo.xyz
- https://yancmo.xyz:5557 → https://connector.yancmo.xyz
- http://136.228.117.217:5557 → https://connector.yancmo.xyz

- http://yancmo.xyz:9090 → https://metrics.yancmo.xyz
- https://yancmo.xyz:9090 → https://metrics.yancmo.xyz
- http://136.228.117.217:9090 → https://metrics.yancmo.xyz

- http://yancmo.xyz:3000 → https://grafana.yancmo.xyz
- https://yancmo.xyz:3000 → https://grafana.yancmo.xyz
- http://136.228.117.217:3000 → https://grafana.yancmo.xyz

Please search through all files in this workspace and:
1. Find all URLs matching the old format (with ports 5550, 5551, 5552, 5553, 5554, 5555, 5557, 9090, 3000)
2. Replace them with the corresponding HTTPS subdomain URLs
3. Update any app name references: clanmap→clashmap, pwa→tracker
4. Show me what files were changed and provide a summary

The server migration is happening soon, so these URL changes are critical for functionality.
```

## Technical Details for Advanced Migration:

### Regex Patterns for Search & Replace:
```regex
# Pattern 1: Domain with port
https?://(yancmo\.xyz|136\.228\.117\.217):5550 → https://dashboard.yancmo.xyz
https?://(yancmo\.xyz|136\.228\.117\.217):5551 → https://cruise.yancmo.xyz
https?://(yancmo\.xyz|136\.228\.117\.217):5552 → https://clashmap.yancmo.xyz
https?://(yancmo\.xyz|136\.228\.117\.217):5553 → https://qsl.yancmo.xyz
https?://(yancmo\.xyz|136\.228\.117\.217):5554 → https://crumb.yancmo.xyz
https?://(yancmo\.xyz|136\.228\.117\.217):5555 → https://tracker.yancmo.xyz
https?://(yancmo\.xyz|136\.228\.117\.217):5557 → https://connector.yancmo.xyz
https?://(yancmo\.xyz|136\.228\.117\.217):9090 → https://metrics.yancmo.xyz
https?://(yancmo\.xyz|136\.228\.117\.217):3000 → https://grafana.yancmo.xyz

# Pattern 2: App name changes
\bclanmap\b → clashmap
\bpwa\b → tracker (context-dependent)
```

### File Types to Check:
- *.html, *.htm
- *.js, *.jsx, *.ts, *.tsx
- *.json (config files)
- *.md, *.txt (documentation)
- *.css, *.scss
- *.php, *.py, *.java
- *.yml, *.yaml (config files)
- .env, .env.*
- README files

### Configuration Files Likely to Need Updates:
- package.json (homepage, scripts)
- .env files (API_URL, BASE_URL)
- config.json, settings.json
- docker-compose.yml (if referencing other services)
- nginx.conf (if local reverse proxy)
- manifest.json (PWA manifests)

## Manual Verification After Migration:

### Test These Common Patterns:
```bash
# Search for remaining port references
grep -r ":5550\|:5551\|:5552\|:5553\|:5554\|:5555\|:5557\|:9090\|:3000" .
grep -r "clanmap" .
grep -r "136.228.117.217" .
```

### Links That Should NOT Be Changed:
- localhost:PORT (local development)
- 127.0.0.1:PORT (local testing)
- Internal Docker network references
- Database connection strings
- SSH connections (port 22)
- FTP connections (port 21, 22)

## Context for Each App:

### Dashboard (Port 5550 → dashboard.yancmo.xyz)
- Main admin interface
- May have links to other services
- Check for hardcoded API endpoints

### Cruise (Port 5551 → cruise.yancmo.xyz)
- Check for inter-service communication
- May reference other apps via URLs

### Clashmap (Port 5552 → clashmap.yancmo.xyz)
- RENAMED from "clanmap"
- Update both URLs AND app name references
- Check for database table names, API endpoints

### QSL (Port 5553 → qsl.yancmo.xyz)
- Check for QSL-specific API calls

### Crumb (Port 5554 → crumb.yancmo.xyz)
- NEW APP - may not have existing references
- Check if other apps link to it

### Tracker (Port 5555 → tracker.yancmo.xyz)
- RENAMED from "pwa"
- Progressive Web App features may reference manifest
- Check service worker URLs

### Connector (Port 5557 → connector.yancmo.xyz)
- API service - likely referenced by other apps
- Check for webhook URLs, API endpoints

### Admin Services:
- Grafana: Port 3000 → grafana.yancmo.xyz
- Prometheus: Port 9090 → metrics.yancmo.xyz