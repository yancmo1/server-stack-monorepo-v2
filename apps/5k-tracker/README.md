# 5K/Marathon Race Tracker PWA

A Progressive Web App (PWA) built with Flask for tracking race times with multi-user support, photo uploads, and statistics. Perfect for runners who want to log their 5K, 10K, half marathon, and marathon times with photos of their achievements.

## Features

- **Progressive Web App**: Install on mobile devices and desktop for app-like experience
- **Offline Support**: Service worker enables offline functionality and caching
- **Multi-User Support**: Individual user accounts with secure authentication
- **Race Tracking**: Log race times for different distances (5K, 10K, Half Marathon, Marathon, Other)
- **Photo Uploads**: Upload photos of race finishes, medals, and bibs
- **Personal Records**: Track your best times for each race distance
- **Statistics Dashboard**: View race statistics and progress over time
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Push Notifications**: Stay engaged with race reminders (when supported)
- **Docker Support**: Easy deployment with Docker containers

## Progressive Web App Features

- 📱 **Installable**: Add to home screen on mobile and desktop
- 🔄 **Offline Capable**: View races and statistics even without internet
- 🚀 **Fast Loading**: Service worker caches assets for instant loading
- 🎨 **Native Feel**: Standalone mode removes browser UI
- 🔔 **Notifications**: Push notifications for race reminders (future feature)
- 🏠 **App Shortcuts**: Quick access to common actions

## Tech Stack

- **Backend**: Flask (Python) with PWA capabilities
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap for styling)
- **PWA**: Service Worker, Web App Manifest, offline caching
- **Deployment**: Docker & Docker Compose with HTTPS support
- **File Uploads**: Secure photo handling with UUID naming

## Quick Start

### Development with PWA Features

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd 5k-tracker
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run with HTTPS (Required for PWA)**
   ```bash
   # For PWA testing, you need HTTPS
   # Option 1: Use the development script
   python run_dev.py
   
   # Option 2: Install mkcert for local HTTPS
   # macOS: brew install mkcert
   # Ubuntu: See PWA-SETUP.md for installation
   mkcert localhost
   python run_dev.py
   ```

4. **Access the PWA**
   - HTTPS: `https://localhost:5001/tracker/` (with mkcert)
   - HTTP: `http://localhost:5000/tracker/` (limited PWA features)
   - Default admin user: `admin` / `admin123`
   - Default test user: `runner` / `runner123`

### Testing PWA Features

1. **Install the PWA**:
   - Chrome/Edge: Look for install icon in address bar
   - iOS Safari: Share → Add to Home Screen
   - Android: "Add to Home Screen" prompt

2. **Test Offline**:
   - Disconnect internet
   - App should still load and show cached data

3. **Service Worker**:
   - Open DevTools → Application → Service Workers
   - Verify registration and status

### Production Deployment (Raspberry Pi)

1. **Clone on your Pi**
   ```bash
   git clone <your-repo-url>
   cd 5k-tracker
   ```

2. **Deploy with Docker**
   ```bash
   docker-compose up -d
   ```

3. **Access via your domain**
   - Configure your domain to point to your Pi
   - Access at `https://yourdomain.com:5011`

## PWA Deployment (Production)

**⚠️ HTTPS is required for PWA features to work properly.**

### Quick Deployment Options

1. **CloudFlare + Any Host**:
   - Deploy to Heroku, DigitalOcean, or similar
   - Add domain to CloudFlare
   - Enable "Always Use HTTPS"
   - PWA features work automatically

2. **Let's Encrypt + Nginx**:
   ```bash
   # Install certbot
   sudo apt install certbot python3-certbot-nginx
   
   # Get certificate
   sudo certbot --nginx -d yourdomain.com
   
   # Configure Nginx (see PWA-SETUP.md for details)
   ```

3. **Docker with Traefik** (Automatic HTTPS):
   - Update docker-compose.yml with Traefik
   - Automatic SSL certificate management
   - See PWA-SETUP.md for full configuration

### PWA Verification Checklist

After deployment, verify:
- [ ] Site loads over HTTPS
- [ ] Service worker registers (check DevTools)
- [ ] Manifest.json is accessible
- [ ] Install prompt appears
- [ ] App works offline
- [ ] Icons display correctly

📋 **For detailed HTTPS setup instructions, see [PWA-SETUP.md](./PWA-SETUP.md)**

## Project Structure

```
5k-tracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── run_dev.py            # Development server with HTTPS support
├── Dockerfile            # Docker container configuration
├── docker-compose.yml    # Docker Compose setup
├── PWA-SETUP.md          # PWA deployment and HTTPS guide
├── .gitignore           # Git ignore rules
├── templates/           # HTML templates
│   ├── base.html        # Base template (PWA-enabled)
│   ├── index.html       # Landing page
│   ├── login.html       # Login form
│   ├── register.html    # Registration form
│   ├── dashboard.html   # User dashboard
│   ├── races.html       # Race listing
│   ├── add_race.html    # Add new race
│   ├── edit_race.html   # Edit race details
│   └── statistics.html  # Race statistics
├── static/              # CSS, JS, and static assets
│   ├── css/
│   │   └── style.css    # Custom styles with PWA enhancements
│   ├── js/
│   │   └── pwa.js       # PWA registration and utilities
│   ├── icons/           # PWA icons
│   │   ├── icon-192x192.png
│   │   ├── icon-512x512.png
│   │   └── favicon-32x32.png
│   ├── manifest.json    # PWA manifest file
│   └── service-worker.js # Service worker for offline support
└── uploads/            # Photo uploads (not in git)
    └── photos/
```

## Database Schema

### Users
- User accounts with authentication
- Profile information (name, email, username)
- Account creation and management

### Races
- Race details (name, type, date, time, location)
- Weather conditions and notes
- Linked to user accounts

### Race Photos
- Photo uploads for each race
- Categorized by type (finish, medal, bib, other)
- Secure file storage with UUID filenames

## Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for sessions
- `UPLOAD_FOLDER`: Directory for photo uploads
- `MAX_CONTENT_LENGTH`: Maximum file upload size

### Docker Configuration
- Runs on port 5011
- Persistent data storage
- Volume mounting for uploads and database

## Security Features

- Password hashing with Werkzeug
- Secure file uploads with extension validation
- User session management
- CSRF protection
- File size limits

## Development Notes

- Developed on macOS for deployment to Raspberry Pi
- SQLite database for simplicity
- Bootstrap for responsive UI
- UUID-based file naming for security

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to modify and distribute.

## Support

For issues or questions, please create an issue in the GitHub repository.
