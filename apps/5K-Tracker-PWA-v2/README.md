# 5K Tracker PWA v2

A modern Progressive Web App for tracking running races and analyzing performance. Built with React, TypeScript, Fastify, and PostgreSQL.

## Features

- 🏃‍♂️ **Race Tracking**: Record and manage your running results (5K, 10K, half marathon, marathon, custom distances)
- 📊 **Analytics**: Visualize your performance with interactive charts and insights
- 🌙 **Dark/Light Mode**: Toggle between themes across all pages
- 📱 **PWA Support**: Installable app with offline capabilities
- 🔐 **Authentication**: Secure user registration and login
- 📈 **Progress Tracking**: Monitor pace trends, PRs, and monthly statistics
- 📂 **Data Import**: Import races from CSV or JSON files
- 🔧 **Admin Dashboard**: User and data management for administrators

## Tech Stack

### Frontend
- **React 19** with TypeScript
- **Vite** for build tooling and dev server
- **Tailwind CSS v4** for styling
- **React Router** for navigation
- **Recharts** for data visualization
- **Lucide React** for icons

### Backend
- **Fastify** with TypeScript
- **Prisma** ORM with PostgreSQL
- **JWT** authentication
- **Zod** for validation
- **bcryptjs** for password hashing

### Development
- **Docker Compose** for PostgreSQL
- **Vitest** for unit testing
- **Playwright** for E2E testing
- **ESLint** and **Prettier** for code quality

## Project Structure

```
5K-Tracker-PWA-v2/
├── SPEC.md                 # Project specification
├── README.md               # This file
├── docker-compose.yml      # PostgreSQL container
├── .gitignore
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── context/        # React context providers
│   │   ├── pages/          # Page components
│   │   └── test/           # Unit tests
│   ├── e2e/               # E2E tests
│   ├── public/            # Static assets, PWA manifest
│   └── package.json
└── server/                # Fastify backend
    ├── src/
    │   ├── routes/        # API route handlers
    │   └── index.ts       # Server entry point
    ├── prisma/
    │   ├── schema.prisma  # Database schema
    │   └── seed.ts        # Database seeding
    ├── .env.example       # Environment variables template
    └── package.json
```

## Quick Start

### Prerequisites

- Node.js 18+ 
- Docker and Docker Compose
- pnpm (for client) or npm/yarn

### 1. Clone and Setup

```bash
git clone <repository-url>
cd 5K-Tracker-PWA-v2
```

### 2. Start Database

```bash
# Start PostgreSQL container
docker compose up -d

# Verify database is running
docker compose ps
```

### 3. Setup Server

```bash
cd server

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Generate Prisma client and run migrations
npx prisma generate
npx prisma db push

# Seed the database with sample data
npm run db:seed

# Start development server
npm run dev
```

The API server will be running at `http://localhost:7778`

### 4. Setup Client

```bash
cd ../client

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

The web app will be running at `http://localhost:7777`

## Development Commands

### Server Commands

```bash
cd server

# Development
npm run dev              # Start dev server with hot reload
npm run build           # Build for production
npm run start           # Start production server

# Database
npm run db:push         # Push schema changes to database
npm run db:migrate      # Create and run migrations
npm run db:seed         # Seed database with sample data
npm run db:studio       # Open Prisma Studio
```

### Client Commands

```bash
cd client

# Development
pnpm dev                # Start dev server
pnpm build              # Build for production
pnpm preview            # Preview production build

# Testing
pnpm test               # Run unit tests
pnpm test:ui            # Run tests with UI
pnpm test:e2e           # Run E2E tests
pnpm test:e2e:ui        # Run E2E tests with UI

# Code Quality
pnpm lint               # Run ESLint
```

## Environment Configuration

### Server (.env)

```bash
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/5k_tracker_v2"
PORT=7778
JWT_SECRET="your-secure-jwt-secret-here"
```

### Client

No environment variables required for local development. The client is configured to connect to the API at `http://localhost:7778`.

## Database Schema

### User Model
- ID, email, password (hashed), name, role
- Timestamps for creation and updates

### Race Model
- ID, user reference, date, distance (decimal km), duration (seconds)
- Calculated pace per km, PR flag, location, region, weather, notes
- Timestamps for creation and updates

### Photo Model (Future)
- ID, race reference, URL, upload timestamp

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - User login
- `POST /api/auth/reset` - Password reset (stub)

### Runs/Races
- `GET /api/runs` - List user's races (with pagination, filtering, sorting)
- `POST /api/runs` - Create new race
- `GET /api/runs/:id` - Get specific race
- `PUT /api/runs/:id` - Update race
- `DELETE /api/runs/:id` - Delete race

### Data Import
- `POST /api/import` - Import races from CSV/JSON

### Health Check
- `GET /api/health` - Service health status

## Testing

### Unit Tests

```bash
cd client
pnpm test
```

Tests are located in `client/src/test/` and use Vitest with React Testing Library.

### E2E Tests

```bash
cd client

# Make sure both client and server are running
pnpm test:e2e
```

E2E tests use Playwright and are located in `client/e2e/`.

## PWA Features

The app includes full PWA support:

- **Manifest**: `/public/manifest.json` with app metadata
- **Service Worker**: `/public/sw.js` for offline caching
- **Install Prompt**: Automatically prompts users to install
- **Offline Support**: Basic offline functionality for cached pages

### Installing the PWA

1. Open the app in a supported browser (Chrome, Edge, Safari)
2. Look for the "Install" prompt or use browser menu → "Install 5K Tracker"
3. The app will be installed and available as a native-like application

## Data Import from V1

### CSV Format

Create a CSV file with the following headers:

```csv
date,distance_km,duration_sec,location,weather,notes,is_pr
2024-01-15,5.0,1392,Central Park,Sunny 18°C,Great run today!,false
2024-01-10,10.0,2910,Brooklyn Bridge,Overcast 15°C,Struggled a bit,true
```

### JSON Format

```json
[
  {
    "date": "2024-01-15",
    "distanceKm": 5.0,
    "durationSec": 1392,
    "location": "Central Park",
    "weather": "Sunny, 18°C",
    "notes": "Great run today!",
    "isPr": false
  }
]
```

### Import Process

1. Navigate to Settings page
2. Click "Import Data"
3. Choose format (CSV or JSON)
4. Upload your file
5. Review import results

## Design Decisions

### Frontend Architecture
- **React with TypeScript**: Type safety and modern React patterns
- **Tailwind CSS v4**: Utility-first styling with the latest features
- **React Router**: Client-side routing for SPA experience
- **Context API**: State management for themes and authentication
- **Recharts**: Declarative charting library for data visualization

### Backend Architecture
- **Fastify**: High-performance Node.js framework
- **Prisma**: Type-safe database ORM with excellent TypeScript support
- **PostgreSQL**: Robust relational database for data integrity
- **JWT**: Stateless authentication suitable for SPAs
- **Zod**: Runtime type validation for API inputs

### Key Tradeoffs
- **Local-only deployment**: Simplified setup vs. production scalability
- **Basic auth**: Simple JWT vs. OAuth/social login
- **SQLite alternative**: PostgreSQL chosen for production-readiness
- **Minimal testing**: Basic coverage vs. comprehensive test suite

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL container is running
docker compose ps

# Restart the database
docker compose down
docker compose up -d

# Check logs
docker compose logs db
```

### Port Conflicts

If ports 7777 or 7778 are in use:

1. Update `client/vite.config.ts` for frontend port
2. Update `server/.env` PORT variable for backend
3. Update `client` API calls if backend port changes

### Prisma Issues

```bash
cd server

# Reset database (⚠️ destructive)
npx prisma migrate reset

# Regenerate client
npx prisma generate

# Push schema without migrations
npx prisma db push
```

## Production Deployment

While this project is designed for local development, here are considerations for production:

1. **Environment Variables**: Use secure secrets and production database
2. **Build Process**: Run `npm run build` for both client and server
3. **Database**: Use managed PostgreSQL service
4. **Security**: Enable HTTPS, add rate limiting, input sanitization
5. **Monitoring**: Add logging, error tracking, and health checks

## Default Users

After running the seed script, you can login with:

- **Admin**: `admin@5ktracker.com` / `admin123`
- **User**: `john@example.com` / `user123`

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new features
3. Update documentation as needed
4. Use conventional commit messages

## Future Enhancements

- Photo uploads for races
- Social features and race sharing
- Training plan recommendations
- Integration with fitness trackers
- Advanced analytics and insights
- Mobile app using Capacitor
- Real-time race tracking

---

## Success Verification

To verify the setup is working correctly:

1. ✅ Database running: `docker compose ps` shows healthy PostgreSQL
2. ✅ Server running: `curl http://localhost:7778/api/health` returns `{"ok": true}`
3. ✅ Client running: Open `http://localhost:7777` and see the dashboard
4. ✅ Add a race: Navigate to Races → Add Race and create a new entry
5. ✅ View analytics: Check that charts render on the Analytics page
6. ✅ Dark mode: Toggle theme using the moon/sun icon in navigation
7. ✅ PWA install: Browser should show install prompt or option

**The development servers are now ready to run locally! 🚀**