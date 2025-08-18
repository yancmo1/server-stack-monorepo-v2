# 5K/Marathon Race Tracker

A Flask web application for tracking race times with multi-user support, photo uploads, and statistics. Perfect for runners who want to log their 5K, 10K, half marathon, and marathon times with photos of their achievements.

## Features

- **Multi-User Support**: Individual user accounts with secure authentication
- **Race Tracking**: Log race times for different distances (5K, 10K, Half Marathon, Marathon, Other)
- **Photo Uploads**: Upload photos of race finishes, medals, and bibs
- **Personal Records**: Track your best times for each race distance
- **Statistics Dashboard**: View race statistics and progress over time
- **Responsive Design**: Works on desktop and mobile devices
- **Docker Support**: Easy deployment with Docker containers

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap for styling)
- **Deployment**: Docker & Docker Compose
- **File Uploads**: Secure photo handling with UUID naming

## Quick Start

### Development (macOS)

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

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the app**
   - Open your browser to `http://localhost:5011`
   - Default admin user: `admin` / `admin123`
   - Default test user: `runner` / `runner123`

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

## Project Structure

```
5k-tracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container configuration
├── docker-compose.yml    # Docker Compose setup
├── .gitignore           # Git ignore rules
├── templates/           # HTML templates
│   ├── base.html        # Base template
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
│   ├── js/
│   └── images/
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
