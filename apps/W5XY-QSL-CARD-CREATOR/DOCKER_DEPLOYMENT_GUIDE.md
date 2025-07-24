# Docker Deployment Guide - QSL Card Creator

## Updated Docker Commands for Database Access

### Problem Resolved
The Docker container was unable to access the Log4OM database because the container was built with a broken symlink. The database file is located at `/Users/yancyshepherd/SyncthingFolders/Log4OM-Database/Log4OM db.SQLite` but the container was trying to access it via a symlink that pointed to a non-existent path inside the container.

### Solution
Use Docker volume mounts to provide direct access to the actual database file.

## Local Development Commands

### 1. Basic Container (Mac/Local)
```bash
# Stop and remove existing container
docker stop qsl-card-creator || true
docker rm qsl-card-creator || true

# Build image
docker build -t qsl-card-creator .

# Run with database volume mount
docker run -d --name qsl-card-creator -p 5001:5001 \
  -v "/Users/yancyshepherd/SyncthingFolders/Log4OM-Database/Log4OM db.SQLite":/app/"Log4OM db.SQLite" \
  qsl-card-creator
```

### 2. Full Container (Mac/Local with Template)
```bash
# Run with both database and template volume mounts
docker run -d --name qsl-card-creator -p 5001:5001 \
  -v "/Users/yancyshepherd/SyncthingFolders/Log4OM-Database/Log4OM db.SQLite":/app/"Log4OM db.SQLite" \
  -v "/path/to/W5XY QSL Card Python TEMPLATE.pdf":/app/"W5XY QSL Card Python TEMPLATE.pdf" \
  qsl-card-creator
```

### 3. Development with Restart Policy
```bash
# For production-like testing with auto-restart
docker run -d --name qsl-card-creator --restart unless-stopped -p 5001:5001 \
  -v "/Users/yancyshepherd/SyncthingFolders/Log4OM-Database/Log4OM db.SQLite":/app/"Log4OM db.SQLite" \
  qsl-card-creator
```

## Raspberry Pi Deployment Commands

### 1. Basic Pi Deployment
The Pi deployment scripts are already configured correctly:
- `deploy_docker_to_pi.sh` - Uses local database and template files
- `deploy_docker_to_pi_fixed.sh` - Fixed version with proper volume mounts
- `deploy_ssl_to_pi.sh` - SSL-enabled version with volume mounts

### 2. Manual Pi Commands
```bash
# On the Raspberry Pi
docker run -d \
    --name qsl-card-creator \
    --restart unless-stopped \
    -p 5001:5001 \
    -v "$(pwd)/Log4OM db.SQLite":/app/"Log4OM db.SQLite" \
    -v "$(pwd)/W5XY QSL Card Python TEMPLATE.pdf":/app/"W5XY QSL Card Python TEMPLATE.pdf" \
    qsl-card-creator-web
```

## Updated Files

The following files have been updated with the correct Docker commands:

1. **README.md** - Main documentation with updated examples
2. **rebuild_docker.sh** - Local rebuild script with database volume mount
3. **.vscode/tasks.json** - VS Code task with database volume mount
4. **deploy_docker_to_pi.sh** - Already had correct volume mounts
5. **deploy_docker_to_pi_fixed.sh** - Already had correct volume mounts
6. **deploy_ssl_to_pi.sh** - Already had correct volume mounts

## Verification

After running any of these commands, verify the database is accessible:

```bash
# Check container logs
docker logs qsl-card-creator

# Expected output should show:
# Database: ✓ Local database available
# Database file: ✓

# Test database access inside container
docker exec qsl-card-creator python -c "import sqlite3; conn = sqlite3.connect('Log4OM db.SQLite'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM Log'); print(f'QSOs: {cursor.fetchone()[0]}'); conn.close()"
```

## Access URLs

- **Local**: http://localhost:5001
- **HTTPS (if SSL configured)**: https://localhost:5001
- **Network**: http://[YOUR_IP]:5001

## Notes

- The database path `/Users/yancyshepherd/SyncthingFolders/Log4OM-Database/Log4OM db.SQLite` is specific to the current Mac setup with Syncthing
- For other environments, adjust the path to point to your actual Log4OM database file
- Volume mounts ensure data persistence and real-time database access
- The container will now show "Database: ✓" in startup logs instead of "Database: ⚠️"
