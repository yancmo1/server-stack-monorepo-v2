# Clan Map Generator

A Flask web application that generates an interactive map visualization of clan members' locations using Folium and OpenStreetMap data.

## Features

- Interactive  world map showing clan member locations
- Geocoding integration with OpenStreetMap Nominatim API
- Responsive web interface
- Docker containerization for easy deployment
- Flask-based web server
- **Postgres database support (shared with Discord bot)**

## Project Structure

```
clan-map/
├── app.py              # Main Flask application
├── map_generator.py    # Map generation logic
├── clan_data.json      # Clan member data (legacy, now synced from DB)
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose for app + Postgres
├── templates/
│   ├── map.html       # Map page
│   ├── members.html   # Members list page
│   ├── submit.html    # Location submission page
│   └── _navbar.html   # Modern navbar partial
└── README.md          # This file
```

## Unified Secrets Management

### Overview
- All secrets are managed in GitHub repository or organization secrets.
- No .env files are used in production or CI/CD.
- Local development uses a script to fetch secrets from GitHub and create a .env file (never committed).

### Local Development
1. Install the GitHub CLI and authenticate:
   ```bash
   gh auth login
   ```
2. Fetch all repository secrets and create a local .env file:
   ```bash
   cd .. # Go to repo root if not already there
   ./fetch_github_secrets.sh
   ```
3. Start the app locally (Docker Compose or manual):
   ```bash
   set -a; source ~/config/.env; set +a; docker compose up --build -d
   # or
   python app.py
   ```

### CI/CD and Server Deployment
- GitHub Actions injects secrets as environment variables.
- Docker Compose and runtime environments read secrets from environment variables.
- No .env files are used or required in production.

### Adding or Updating Secrets
- Always add or update secrets in the GitHub repository settings.
- For local development, re-run `./fetch_github_secrets.sh` after updating secrets.

### Security
- Never commit .env files or secrets to the repository.
- Only use .env for local development.

---

For more details, see the official [GitHub Actions secrets documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets).

## Installation & Setup

### Local Development (with Docker Compose)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd clan-map
   ```

2. **Start the app and Postgres using Docker Compose:**
   ```bash
   set -a; source ~/config/.env; set +a; docker compose up --build -d
   ```
   This will start both the Flask app and a local Postgres database.

3. **Access the application:**
   Open your browser and navigate to `https://localhost:5552`

### Manual Local Development (without Docker)

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables for Postgres connection:**
   ```bash
   export POSTGRES_DB=cocstack
   export POSTGRES_USER=cocuser
   export POSTGRES_PASSWORD=yourpassword
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   Open your browser and navigate to `http://localhost:5552`

## Database Configuration

- The app uses a shared Postgres database (same as the Discord bot).
- Connection is configured via environment variables:
  - `POSTGRES_DB`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_HOST`
  - `POSTGRES_PORT`
- When using Docker Compose, these are set automatically.

## Docker Compose

The provided `docker-compose.yml` will start both the Flask app and a local Postgres database for development/testing. Data is persisted in a Docker volume.

## API Integration

The application uses the OpenStreetMap Nominatim API for geocoding locations. No API key is required, but please be respectful of rate limits.

## Dependencies

- **Flask:** Web framework
- **Folium:** Interactive map generation
- **psycopg2-binary:** Postgres database driver
- **Requests:** HTTP client for geocoding API
- **Gunicorn:** Production WSGI server (Docker only)

## Development

### Adding New Features

1. Modify `map_generator.py` for map-related functionality
2. Update `app.py` for new routes or Flask configurations
3. Use the web UI or sync scripts to update member information

### Testing

The application can be tested locally using Docker Compose or the Flask development server.

## Production Considerations

- The Docker container uses Gunicorn with 2 workers
- The application runs as a non-root user for security
- Consider implementing caching for geocoding results in high-traffic scenarios
- Rate limiting may be needed for the geocoding API
- **Production should set Postgres environment variables to point to the production DB**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

## Support

[Add contact information or support channels here]
