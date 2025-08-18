Role

You are an expert full-stack engineer and UI/UX designer. Build a modern, lightweight PWA for tracking running events and performance. Architect it so it can later be packaged as a native iOS app for the App Store.

Task

Rebuild the app from scratch as 5K Tracker V2 (supporting 5K, 10K, half, full, etc., but keep the brand “5K Tracker” for now).

Create a new project in a folder named 5K-Tracker-PWA-V2.

Local Docker Deployment, dev only on port 7777. Don’t deploy or touch other services/ports.

Use PostgreSQL with migrations and seed data.

Deliver a fresh, responsive UI/UX with working dark/light mode.

Implement PWA features: manifest, service worker, install prompt, icons.

Provide a simple data import path for V1 later (CSV/JSON/import endpoint).

Include tests and a clean README with all commands.

Context
Recommended Stack (justify changes in README if you deviate)

Frontend: React + Vite, TypeScript, Tailwind, shadcn/ui

Backend: Node.js (TypeScript) with Fastify (or Express)

DB/ORM: PostgreSQL + Prisma (or Drizzle)

PWA: manifest.json + service worker

Testing: Vitest/Jest; basic Playwright (or similar) happy-path E2E

Tooling: ESLint, Prettier

Core Features (User)

Auth: register, login, logout, password reset, profile edit

Race Management: add/edit/delete results (date, distance, duration, pace, location, weather, notes, PR flag, region)

List: sortable/filterable/searchable race list; details page

Photos: upload per race (basic)

Workouts: A page to import workouts from IOS or input data like time and milage on the treadmill or outside. Give option to choose. When app is ready for app store we'll incorporate healthkit. 



Import: CSV/JSON import (stub is fine for V2)

Dashboard & Analytics:

Monthly races count

Average pace/time over time

Personal Records (PRs) summary

Runs per region (if data available)

Admin

Admin dashboard (users, races, system overview)

Manage users (add/edit/delete, reset password, role)

View/manage all races

Import/export data

API & Data Model (initial)

Run

id (uuid), user_id (uuid)

date (datetime), distance_km (number; support 5K/10K/21.0975/42.195, etc.)

duration_sec (int), pace_sec_per_km (computed or stored)

region (string, optional), location (string, optional), weather (string, optional)

notes (text, optional), is_pr (boolean)

created_at, updated_at

User

id, email, password_hash, name, role (user/admin), created_at, updated_at

Photo

id, race_id, file_path/url, upload_date

Dev/Env

Run on port 7777

Provide .env.example; load .env (never commit secrets)

Optional Dockerfile/docker-compose

SSL-ready (for future), but local-only now

Security

Password hashing, secure sessions/JWT

Role/route protection

CSRF protection if forms are used

HTTPS ready for future deploy

iOS Future-Readiness

Keep web app PWA-clean and modular so it can later wrap with Capacitor or React Native bridge

Keep assets, routing, and storage choices mobile-friendly

Output

Produce in this session:

New scaffold in 5K-Tracker-PWA-V2

Pages:

Auth (Login, Register, Reset)

Dashboard (default route)

Races (list/detail/add/edit)

Analytics (3+ charts as above)

Profile, Settings

Admin (users + data)

PWA: manifest, service worker, app icons, install prompt

Theming: working dark/light toggle

Postgres schema, migrations, seed data

Import stub/endpoint for V1 CSV/JSON

README.md: install/dev/test/build/migrate/seed instructions

Tests: unit + 1 happy-path E2E

Short design decisions section in README (stack choices, tradeoffs)

Rules

Don’t deploy; local only on port 7777

Don’t break other services/ports

Keep narration minimal; build and show working features

If deviating from stack, explain briefly in README