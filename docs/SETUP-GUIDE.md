
# YANCY Monorepo Setup Guide

## Prerequisites
- macOS or Ubuntu with Docker and Docker Compose installed
- VS Code (recommended)
- SSH access to your server (for production)

## Folder Structure
- `apps/` — All major apps and services
- `shared/` — Shared configs, SSL certs, templates, scripts
- `deploy/` — Deployment files (Docker, systemd, nginx)
- `docs/` — Documentation and guides
- `archive/` — Legacy and backup files

## Local Development Setup
1. Clone the repo and open in VS Code:
	```bash
	git clone <your-repo>
	cd YANCY
	```
2. Install dependencies for each app in `apps/` (see each app’s README).
3. Copy `.env.example` to `.env` and update values as needed for each app.
4. Use Docker Compose in `deploy/` to run services locally:
	```bash
	cd deploy
	docker-compose up -d --build
	docker-compose ps
	```
5. Access your services at the configured ports (see each app’s README).

## Shared Database Setup
- To share data between apps, configure each app to use the same Postgres connection (see `shared/config/` or `.env`).
- For SQLite, ensure the database file is accessible to all apps that need it.

## Production Deployment
1. SSH into your server.
2. Pull the latest code:
	```bash
	git pull
	```
3. Update environment variables in `.env` or `shared/config/`.
4. Use Docker Compose in `deploy/` to build and run services.

## Backups & Archiving
- Use scripts in `shared/scripts/` for backups.
- Move old or backup files to `archive/` to keep the workspace clean.

## Troubleshooting
- See `docs/TROUBLESHOOTING_GUIDE.md` for common issues and solutions.
- **Clash Map**: https://clashmap.yancmo.xyz
- **QSL Card Creator**: https://qsl.yancmo.xyz

### 5. **Monitoring (If Prometheus/Grafana already installed)**
- **Prometheus**: https://metrics.yancmo.xyz
- **Grafana**: https://grafana.yancmo.xyz

## 🔧 **Configuration Details**

### **Discord Bot Setup**
```bash
cd coc-discord-bot
cp .env.example .env
nano .env
```

Add your Discord bot token and other required settings.

### **SSL Certificates (Production)**
Place your SSL certificates in the `ssl/` directory:
```bash
ssl/
├── cert.pem
└── key.pem
```

## 📊 **Monitoring Setup**

### **Prometheus Targets**
Your apps automatically expose metrics at `/metrics` endpoint:
- Dashboard: `dashboard.yancmo.xyz/metrics`
- Cruise Price Check: `cruise.yancmo.xyz/metrics`
- Clash Map: `clashmap.yancmo.xyz/metrics`
- QSL Card Creator: `qsl.yancmo.xyz/metrics`

### **Grafana Dashboards**
1. Add Prometheus as data source: `https://metrics.yancmo.xyz`
2. Import dashboards from Grafana marketplace
3. Monitor your Flask apps, Docker containers, and system metrics

## 🔍 **Troubleshooting**

### **Check Service Status**
```bash
# On your Ubuntu server
docker-compose ps
docker-compose logs <service-name>
```

### **Common Issues**
1. **Port conflicts**: Ensure ports 5550-5553 are available
2. **SSL issues**: Check certificate paths and permissions
3. **Database issues**: Ensure data directories are writable

### **Health Checks**
```bash
# Test all services
curl https://dashboard.yancmo.xyz/health
curl https://cruise.yancmo.xyz/health
curl https://clashmap.yancmo.xyz/health
curl https://qsl.yancmo.xyz/health
```

## 🧹 **Cleanup Old Pi Files**
```bash
# Remove old Pi-specific files (see CLEANUP-CHECKLIST.md)
# Make backup first
tar -czf pi-migration-backup.tar.gz cruise-price-check/tailscale* cruise-price-check/deploy_to_pi*

# Remove files listed in CLEANUP-CHECKLIST.md
```

## 🔄 **Updates and Maintenance**
```bash
# Update and redeploy
git pull
./deploy-to-server.sh

# View logs
ssh your-user@your-server-ip
cd /opt/apps
docker-compose logs -f
```

## 🎯 **Next Steps**
1. Set up reverse proxy (Nginx) for custom domains
2. Configure automatic SSL renewal (Let's Encrypt)
3. Set up log rotation and monitoring alerts
4. Configure backups for databases and configurations

---

**🎉 Your server stack is now ready for production!**
