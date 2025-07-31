# Development & Deployment Quick Reference

## 🚀 Development Commands

### Start Development Environment
```bash
./deploy/dev.sh start
```
- Starts all services locally
- Dashboard: http://localhost:5550
- Tracker: http://localhost:5554
- All other apps on their respective ports

### Development Management
```bash
./deploy/dev.sh stop          # Stop all services
./deploy/dev.sh restart       # Restart all services
./deploy/dev.sh test          # Run health checks
./deploy/dev.sh status        # Show container status
./deploy/dev.sh logs          # Show all logs
./deploy/dev.sh logs tracker  # Show tracker logs only
./deploy/dev.sh clean         # Complete cleanup
```

### Service-Specific Development
```bash
./deploy/dev.sh restart tracker     # Restart just tracker
./deploy/dev.sh restart dashboard   # Restart just dashboard
./deploy/dev.sh logs dashboard      # Dashboard logs only
```

## 🌐 Production Deployment

### Deploy Everything
```bash
./deploy/deploy.sh all "Your commit message"
```

### Deploy Specific Services
```bash
./deploy/deploy.sh tracker "Fixed login bug"
./deploy/deploy.sh dashboard "Updated monitoring"
./deploy/deploy.sh no-bot "Deploy without Discord bot"
```

### Check Production Status
```bash
./deploy/deploy.sh status
```

## 📋 VS Code Tasks

Use **Ctrl+Shift+P** → **Tasks: Run Task** and select:

### Development Tasks
- 🚀 **Dev: Start All** - Start development environment
- 🛑 **Dev: Stop All** - Stop development environment  
- 🔄 **Dev: Restart All** - Restart all services
- 🧪 **Dev: Test Environment** - Run health checks
- 📊 **Dev: Show Status** - Container status
- 📋 **Dev: Show Logs** - All logs
- 🔄 **Dev: Restart Tracker** - Restart tracker only
- 🔄 **Dev: Restart Dashboard** - Restart dashboard only
- 📋 **Dev: Tracker Logs** - Tracker logs only
- 📋 **Dev: Dashboard Logs** - Dashboard logs only

### Production Tasks
- 🌐 **Deploy: All to Production** - Deploy everything
- 🏃 **Deploy: Tracker Only** - Deploy tracker only
- 🏠 **Deploy: Dashboard Only** - Deploy dashboard only
- 🚫 **Deploy: All (No Bot)** - Deploy without Discord bot
- 📊 **Deploy: Check Server Status** - Check production status

## 🎯 Recommended Workflow

### For Development
1. `./deploy/dev.sh start` - Start local environment
2. Make your changes
3. `./deploy/dev.sh test` - Test changes locally
4. `./deploy/dev.sh restart [service]` - Restart specific service if needed

### For Production Deployment
1. Test locally first with development environment
2. `./deploy/deploy.sh [service] "Description of changes"`
3. `./deploy/deploy.sh status` - Verify deployment

### Stable vs Development Apps
- **Stable**: `tracker`, `dashboard` - Won't show rebuild controls in dashboard
- **Development**: Other apps - Show start/stop/rebuild controls

## 📁 File Organization

```
deploy/
├── dev.sh              # 🚀 Development environment manager
├── deploy.sh           # 🌐 Production deployment script  
├── test-dev.sh         # 🧪 Development testing
├── docker-compose.yml  # Production configuration
└── docker-compose.dev.yml # Development configuration

scripts/
├── backup_to_meganz.sh     # Backup utilities
├── server_audit.sh         # System monitoring
└── send_backup_log_test_email.py # Email notifications

archive/old-scripts/
└── [Old redundant scripts moved here]
```

## 🔧 Troubleshooting

### Port Conflicts
```bash
lsof -ti:5550  # Check what's using port 5550
kill -9 $(lsof -ti:5550)  # Kill process on port 5550
```

### Clean Reset
```bash
./deploy/dev.sh clean  # Remove all dev containers/volumes
docker system prune -a  # Clean all Docker resources
```

### Server Issues
```bash
./deploy/deploy.sh status  # Check server status
ssh yancmo@ubuntumac "cd server-stack-monorepo-v2/deploy && docker compose logs"
```
