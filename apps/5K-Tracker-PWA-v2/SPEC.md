# 5K Tracker V2 — Prompt-Structure Spec (`SPEC.md`)

> **Intent:** This spec is written for an AI agent (Copilot / GPT-5) to follow as a blueprint.  
> **Scope:** Fresh rebuild of the app as a modern PWA; future-ready for iOS packaging, but **local only** for now.

## Role
You are an expert full-stack engineer and UI/UX designer. Build a clean, maintainable, installable **PWA** that tracks running events (5K, 10K, half, full, etc.) with analytics. Architect it so it can later be packaged for the iOS App Store (e.g., with Capacitor).

## Task
Create a brand-new project in a new folder: **`5K-Tracker-PWA-V2`**.  
Deliver a working local app with: auth, race CRUD, dashboard & analytics, responsive UI with dark/light mode, PWA features, Postgres with migrations/seed, basic tests, and a documented import path for V1 data.

## Constraints
- **Local only.** Do **not** deploy.  
- **Ports:** Web (Vite) **:7777**, API **:7778**, Postgres **:5432** (via Docker).  
- Keep narration minimal—**build and verify**.  
- Do not touch other services/ports.  
- Use `.env` (provide `.env.example`) and do not commit secrets.  
- Use **pnpm** consistently for the frontend to avoid package manager conflicts.

---

## Recommended Tech Stack (justify deviations in README)
- **Frontend:** React + Vite, **TypeScript**, Tailwind CSS (v4), shadcn/ui (optional)  
- **Tailwind v4 CLI:** `@tailwindcss/cli` (not the old `tailwindcss` bin)  
- **Backend:** Node.js (TypeScript) with **Fastify** (or Express), Zod  
- **DB/ORM:** PostgreSQL + **Prisma** (migrations + seed)  
- **PWA:** `manifest.json`, service worker, install prompt, app icons  
- **Testing:** Vitest/Jest (unit) + one happy-path E2E (e.g., Playwright)  
- **Tooling:** ESLint, Prettier

---

## Project Structure (target)
```
5K-Tracker-PWA-V2/
  SPEC.md
  README.md
  .gitignore
  docker-compose.yml
  client/            # React + Vite + TS + Tailwind
    index.html
    src/
      main.tsx
      App.tsx
      index.css      # @tailwind base; @tailwind components; @tailwind utilities
      pages/         # Dashboard, Races (list/detail/new/edit), Analytics, Profile, Settings, Admin
      components/    # UI pieces
    tailwind.config.js
    postcss.config.js
    tsconfig.json
    vite.config.ts
    package.json
  server/            # Fastify + TS + Prisma
    src/
      index.ts       # health route, mount routes
      routes/
        runs.ts      # CRUD for races
        auth.ts
        import.ts    # stub for V1 import
    prisma/
      schema.prisma
      migrations/
      seed.ts
    .env.example
    package.json
```

---

## Pages & Routes (minimum)
- **`/` → Dashboard** (default): key stats, quick links  
- **`/races`**: list/search/sort/filter; row → detail  
- **`/races/new`**, **`/races/:id`** (detail + edit/delete)  
- **`/analytics`**: charts (see below)  
- **`/profile`**, **`/settings`**  
- **`/admin`**: user & data management (basic)

---

## Features

### User
- **Auth:** register/login/logout, password reset, profile edit  
- **Race Management:** add/edit/delete race results with fields:
  - `date`, `distance_km` (support 5K, 10K, 21.0975, 42.195, custom), `duration_sec`, `pace_sec_per_km` (compute/store), `region`, `location`, `weather`, `notes`, `is_pr`  
- **List Views:** sortable, filterable, searchable; clean alignment  
- **Photos:** upload per race (basic)  
- **Import:** CSV/JSON import (stub endpoint + README instructions)

### Admin
- Admin dashboard (users, races, system overview)  
- Manage users (add/edit/delete, role)  
- View/manage all races  
- Import/export data

### Analytics (minimum 3 charts)
- **Monthly runs count** (last 12–18 months)  
- **Average pace/time trend**  
- **PRs summary** (count, most recent)  
- Optional: runs per region; distance distribution

### UI/UX
- New visual style (not like V1)  
- Responsive (mobile → desktop)  
- **Dark/light mode** working everywhere  
- Clean, accessible nav (Dashboard, Races, Analytics, Settings, Admin)

---

## API & Data Model

### REST Endpoints (server)
- `GET /api/health`
- **Runs:** `GET /api/runs` (query: paging, sort, filters), `POST /api/runs`, `GET /api/runs/:id`, `PUT /api/runs/:id`, `DELETE /api/runs/:id`
- **Auth:** `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/reset`
- **Import:** `POST /api/import` (CSV/JSON), no heavy validation required in V2

### Prisma Models (baseline)
```prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  password  String
  name      String?
  role      String   @default("user")
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  races     Race[]
}

model Race {
  id          String   @id @default(uuid())
  user        User     @relation(fields: [userId], references: [id])
  userId      String
  date        DateTime
  distanceKm  Decimal  @db.Decimal(6,2)   // supports ultras
  durationSec Int
  paceSecPerKm Int?
  isPr        Boolean  @default(false)
  region      String?
  location    String?
  weather     String?
  notes       String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  photos      Photo[]
}

model Photo {
  id        String   @id @default(uuid())
  race      Race     @relation(fields: [raceId], references: [id])
  raceId    String
  url       String
  uploaded  DateTime @default(now())
}
```

---

## PWA Requirements
- `manifest.json` with icons and app metadata  
- Service worker: offline shell caching (basic)  
- Install prompt behavior  
- Verify PWA install on desktop & iOS Safari (add to Home Screen)

---

## Security (V2 level)
- Password hashing; safe session/JWT handling  
- Basic role/route protection (user/admin)  
- CSRF protection (if server-rendered forms are used)  
- HTTPS ready in config for future deploy (local remains HTTP)

---

## Testing
- Unit tests for core utilities & endpoints  
- One **happy-path E2E**: register → add run → see on dashboard → open analytics

---

## Data Import (from V1)
- Add **`POST /api/import`** (accept CSV/JSON) with a mapping table in README  
- Provide example import files  
- Basic validation and conflict strategy documented in README

---

## Dev Environment & Ports
- **Web (client):** Vite dev server on **:7777**  
- **API (server):** Fastify dev server on **:7778**  
- **DB:** Postgres **:5432** (Docker Compose)  
- Provide `.env.example` in `server/` with `DATABASE_URL` and `API_PORT`

---

## Package Manager & Tailwind (Important)
Use **pnpm** in `client/`. Tailwind **v4** requires the **new CLI** package.

- Add dev deps:
  ```
  pnpm add -D tailwindcss @tailwindcss/cli postcss autoprefixer
  ```
- Initialize configs (either works):
  ```
  pnpm exec tailwindcss init -p
  # or
  pnpm dlx @tailwindcss/cli@latest init -p
  ```
- `tailwind.config.js`
  ```js
  /** @type {import('tailwindcss').Config} */
  export default {
    content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
    theme: { extend: {} },
    plugins: [],
  };
  ```
- `postcss.config.js`
  ```js
  export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
  ```
- `src/index.css` (top of file)
  ```css
  @tailwind base;
  @tailwind components;
  @tailwind utilities;
  ```

> If you intentionally want Tailwind **v3**, pin `tailwindcss@^3` and use the legacy `tailwindcss` CLI. Otherwise, prefer v4 + `@tailwindcss/cli`.

---

## Docker Compose (DB)
Create `docker-compose.yml` at repo root:
```yaml
services:
  db:
    image: postgres:16
    container_name: 5k_v2_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: 5k_tracker_v2
    ports:
      - "5432:5432"
    volumes:
      - pgdata_v2:/var/lib/postgresql/data
volumes:
  pgdata_v2:
```

---

## .gitignore (root)
```gitignore
# deps & build
node_modules/
dist/
build/
.next/
out/
coverage/
*.log
*.tsbuildinfo

# env & local
.env
.env.*
!.env.example

# editor
.vscode/
.DS_Store

# prisma
prisma/*.db
prisma/migrations/*-tmp/

# backups
archive/
**/backups/

# lockfiles (pick one PM; remove the others)
package-lock.json
yarn.lock
# keep pnpm (or remove if you standardize differently)
# pnpm-lock.yaml
```

---

## README Tasks (have the agent generate)
- Install/run instructions (client/server)  
- Environment setup (`.env.example` → `.env`)  
- Migrations & seed  
- PWA testing notes  
- Import instructions for V1 data  
- Testing commands  
- Design decisions (stack choices, tradeoffs)

---

## Agent Kickoff Prompt (paste into Copilot Chat)
```
Read SPEC.md in the workspace and scaffold the entire project exactly as specified:
- Create client (React+Vite+TS+Tailwind v4) on port 7777 and server (Fastify+TS+Prisma) on port 7778.
- Set up Postgres via docker-compose.yml, Prisma schema/migrations/seed, and .env.example in /server.
- Implement pages and routes, API endpoints, basic tests, PWA manifest and SW, dark/light mode, and 3+ analytics charts.
- Generate a complete README with install/dev/test/build/migrate/seed and V1 import instructions.
- Minimize narration; confirm when dev servers are ready to run locally.
```

---

### Success Criteria (what to verify manually)
- `docker compose up -d` brings up Postgres  
- `server` runs on **:7778** and `GET /api/health` returns `{ ok: true }`  
- `client` runs on **:7777**, Tailwind styles load  
- You can add a race and see it in the list & dashboard  
- Analytics page renders charts  
- Dark/light mode works  
- README has all commands and import instructions

---

When you’re ready to add AI features later (summary, training plans, etc.), we can extend this with a small **“AI Readiness”** section and wire in MCP + Postgres—but for V2 this is intentionally out of scope.
