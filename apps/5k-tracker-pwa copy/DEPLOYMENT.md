# Deployment Guide

## Setting Up GitHub Repository

1. **Create a new repository on GitHub**
   - Go to https://github.com/new
   - Repository name: `5k-race-tracker` (or your preferred name)
   - Description: "Flask web app for tracking marathon and 5K race times with photo uploads"
   - Set to Public or Private as desired
   - Don't initialize with README (we already have one)

2. **Connect your local repository to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

## Development Workflow (macOS)

1. **Local Development**
   ```bash
   # Clone the repo (if starting fresh)
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME
   
   # Set up Python environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Run locally
   python app.py
   # Access at http://localhost:5011
   ```

2. **Making Changes**
   ```bash
   # Make your changes
   # Test locally
   
   # Commit and push
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

## Production Deployment (Raspberry Pi)

### Option 1: Direct Deployment

1. **On your Raspberry Pi:**
   ```bash
   # Install Docker if not already installed
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   # Log out and back in
   
   # Install Docker Compose
   sudo pip3 install docker-compose
   
   # Clone your repository
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME
   
   # Deploy with Docker
   docker-compose up -d
   ```

2. **Update Deployment:**
   ```bash
   cd YOUR_REPO_NAME
   git pull origin main
   docker-compose down
   docker-compose up -d --build
   ```

### Option 2: Automated Deployment with Git Hooks

1. **Set up a deploy script on your Pi:**
   ```bash
   # Create deploy script
   nano ~/deploy-race-tracker.sh
   ```

   Add this content:
   ```bash
   #!/bin/bash
   cd /path/to/your/5k-race-tracker
   git pull origin main
   docker-compose down
   docker-compose up -d --build
   echo "Deployment completed at $(date)"
   ```

   Make it executable:
   ```bash
   chmod +x ~/deploy-race-tracker.sh
   ```

2. **Deploy by running:**
   ```bash
   ~/deploy-race-tracker.sh
   ```

## Domain Configuration

1. **Configure your domain/subdomain to point to your Pi's IP**
2. **Set up reverse proxy (nginx) if needed:**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:5011;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **For HTTPS, use Let's Encrypt:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## Environment Variables for Production

Create a `.env` file on your Pi (don't commit this):
```env
SECRET_KEY=your-very-secure-secret-key-here
FLASK_ENV=production
DATABASE_URL=sqlite:///race_tracker.db
```

Update your docker-compose.yml to use these:
```yaml
environment:
  - SECRET_KEY=${SECRET_KEY}
  - FLASK_ENV=${FLASK_ENV}
```

## Backup Strategy

1. **Database Backup:**
   ```bash
   # Create backup script
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   cp /path/to/race_tracker.db /backups/race_tracker_$DATE.db
   
   # Keep only last 30 days
   find /backups -name "race_tracker_*.db" -mtime +30 -delete
   ```

2. **Photo Backup:**
   ```bash
   # Backup uploads directory
   tar -czf /backups/uploads_$DATE.tar.gz /path/to/uploads/
   ```

3. **Automated Backups with Cron:**
   ```bash
   # Add to crontab (crontab -e)
   0 2 * * * /path/to/backup-script.sh
   ```

## Monitoring

1. **Check if service is running:**
   ```bash
   docker-compose ps
   curl http://localhost:5011/
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Resource monitoring:**
   ```bash
   docker stats
   ```

## Security Considerations

1. **Change default passwords** in production
2. **Use strong SECRET_KEY**
3. **Regular updates:**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```
4. **Firewall configuration:**
   ```bash
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw allow 5011  # Your app (if direct access)
   sudo ufw enable
   ```

## Troubleshooting

1. **Port already in use:**
   ```bash
   sudo lsof -i :5011
   sudo kill -9 PID
   ```

2. **Docker issues:**
   ```bash
   docker system prune -a
   docker-compose down --volumes
   docker-compose up -d --build
   ```

3. **Database issues:**
   ```bash
   # Reset database (WARNING: loses all data)
   rm race_tracker.db
   docker-compose restart
   ```

4. **Permission issues:**
   ```bash
   sudo chown -R $USER:$USER /path/to/project
   chmod -R 755 /path/to/project
   ```
