# 5K Tracker App Specification (V1)

## Overview
The 5K Tracker is a web application for runners to log, track, and analyze their 5K race performances. It supports user registration, race result management, statistics, and admin controls. The app is designed as a PWA (Progressive Web App) and supports secure deployment with SSL.

---

## 1. User Features

### 1.1. Authentication & User Management
- User registration (with email/password)
- Login/logout
- Password reset (forgot/reset password flow)
- User profile page (view/edit personal info)
- Admin user management (add/edit/delete users)

### 1.2. Race Management
- Add new race results (date, time, location, weather, notes, etc.)
- Edit/delete existing race results
- View list of all races (sortable, filterable)
- Import race results (CSV or similar)
- Race photos upload (per race)

### 1.3. Statistics & Dashboard
- Dashboard with summary stats (total races, best time, average pace, etc.)
- Detailed statistics page (charts, trends, personal records)
- Weather and other metadata tracking per race

### 1.4. PWA Features
- Installable on mobile/desktop
- Offline support (service worker)
- App manifest for PWA compliance
- Custom icons and splash screens

### 1.5. UI/UX
- Responsive design (mobile/desktop)
- Themed UI (dark/light, if supported)
- Navigation bar/menu
- Error and success notifications

---

## 2. Admin Features
- Admin dashboard (overview of users, races, system status)
- Manage users (view, add, edit, delete)
- View all race results (all users)
- Import/export data

---

## 3. Pages & Templates
- `index.html`: Landing page
- `login.html`, `register.html`, `forgot_password.html`, `reset_password.html`: Auth flows
- `dashboard.html`: User dashboard
- `races.html`: List of races
- `add_race.html`, `edit_race.html`: Race management
- `statistics.html`: Stats and charts
- `profile.html`: User profile
- `settings.html`: App/user settings
- `photos.html`: Race photos
- `admin/`: Admin dashboard and user management
- `base.html`: Shared layout

---

## 4. Backend/API
- Python (Flask or similar)
- RESTful endpoints for all CRUD operations (users, races, stats)
- Authentication endpoints (login, register, password reset)
- File upload endpoints (photos)
- Data import/export endpoints
- Database: likely SQLite (can be upgraded)

---

## 5. Data Models
- **User**: id, email, password_hash, name, admin flag, etc.
- **Race**: id, user_id, date, time, location, weather, notes, photos, etc.
- **Photo**: id, race_id, file_path, upload_date, etc.

---

## 6. Deployment & Configuration
- Dockerized deployment (Dockerfile, docker-compose)
- SSL support (Cloudflare, local certs)
- Environment variable configuration
- Scripts for setup, start, verify, and update
- Requirements.txt for Python dependencies

---

## 7. Security
- Password hashing
- Secure session management
- CSRF protection (if forms)
- HTTPS/SSL enforced
- Admin access control

---

## 8. Integrations & Advanced Features
- PWA: manifest.json, service worker (sw.js)
- Cloudflare SSL (optional)
- Data import/export (CSV, etc.)
- Automated deployment scripts

---

## 9. Best Practices & V2 Suggestions
- Modularize backend (blueprints, services)
- Use modern frontend framework (React/Vue/Svelte) for V2
- Upgrade database for scalability (Postgres, etc.)
- Add API versioning
- Improve test coverage (unit/integration tests)
- Enhance accessibility and mobile UX

---

## 10. File Structure (Key Files)
- `app.py`: Main app entry point
- `requirements.txt`: Python dependencies
- `Dockerfile`, `docker-compose.yml`: Deployment
- `static/`: CSS, icons, images
- `templates/`: HTML templates
- `uploads/`: User-uploaded photos
- `migrations/`: DB migrations
- `scripts/`: Utility and deployment scripts

---

## 11. Notes
- All features above should be preserved or improved in V2.
- Use this spec as a baseline for planning, estimation, and migration.
- Refer to the current codebase for implementation details as needed.
