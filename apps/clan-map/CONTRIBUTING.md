# Contributing to Clan Map Generator

Thank you for your interest in contributing to the Clan Map Generator project!

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/clan-map.git
   cd clan-map
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Development Workflow

1. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test them:
   ```bash
   make test
   make dev  # Test locally
   ```

3. **Build and test with Docker**:
   ```bash
   make build
   make run
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: description of your changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## Code Guidelines

- Follow PEP 8 Python style guidelines
- Add comments for complex logic
- Update documentation for new features
- Test your changes thoroughly

## Adding New Features

### Adding New Map Features
- Modify `map_generator.py` for map-related functionality
- Update `clan_data.json` structure if needed
- Update the README if new configuration is required

### Adding New Routes
- Add routes to `app.py`
- Update templates if UI changes are needed
- Document new endpoints in the README

### Docker Changes
- Test Docker builds locally: `make build`
- Update `docker-compose.yml` if needed
- Test with `make compose-up`

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Error messages
- Expected vs actual behavior

## Questions?

Feel free to open an issue for questions or suggestions!
