# Move My Car (self‑hosted, privacy‑friendly)

[中文文档 / Chinese README](readme_zh.md)

Open‑source, self‑hosted “move my car” QR tool. Visitors can contact the car owner anonymously without exposing a phone number. MVP covers: code management, anonymous messages (text + image), lightweight notifications (Bark), abuse protection (rate limit + per‑code blacklist), and printable/online QR codes.

## Tech Stack
- Python 3.12, FastAPI, Starlette, Uvicorn
- SQLAlchemy 2.x, SQLite (default)
- Jinja2 templates, Segno (QR), httpx

## Quick Start
- Docker (recommended)
  - Copy config: `cp .env.example .env`
  - Start: `docker compose up -d`
  - Open: `http://localhost:8000/login` (default admin `admin/admin`)
- Local (no Docker)
  - Create venv: `python -m venv .venv && source .venv/bin/activate`
  - Install deps: `pip install -r requirements.txt`
  - If you want the app to auto‑load `.env`: `export LOAD_ENV_FILE=1 && cp .env.example .env`
  - Run: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
  - Open: `http://127.0.0.1:8000/login`

Notes
- The app does NOT auto‑load `.env` by default (to keep tests reproducible). Set `LOAD_ENV_FILE=1` to enable.
- SQLite lives under `data/`; uploads under `data/uploads/`. Docker maps `./data` as a volume.

## Features
- Manage multiple codes (activate/pause/delete, optional display name)
- Printable QR and direct PNG (`/qr/{public_code}.png?scale=10&border=2`)
- Landing page `/c/{public_code}` for anonymous messages (text + 1 image ≤ 5 MB)
- Dashboard with latest messages; mark as processed
- Optional Bark push per code
- Rate limiting + per‑code blacklist

## Configuration (env)
- `APP_SECRET`: Session signing key (change in production)
- `APP_BASE_URL`: Public base URL (used by printable page and QR)
- `DB_URL`: DB URL (default `sqlite:///data/app.db`)
- `DATA_DIR`: Data folder for DB/uploads (default `./data`)
- `MAX_IMAGE_MB`: Max upload image size in MB (default `5`)
- `RATE_LIMIT_WINDOW`/`RATE_LIMIT_COUNT`: Rate limit window/quota (default `60`/`1`)
- `ANON_CHAT_ENABLED`: Optional real‑time chat toggle (MVP: simple message; default `false`)
- `ADMIN_USERNAME`/`ADMIN_PASSWORD`: Admin bootstrap (non‑test runtime)

Testing behavior
- In pytest or when using `.../data/test.db`, admin credentials are forced to `admin/admin` to avoid host `.env` interference.

## Project Structure
- `app/`: FastAPI backend + Jinja2 templates
- `app/routes/`: Page and API routes
- `app/services/`: Rate limit, notifications, helpers
- `app/templates/`: HTML pages; `app/style.css`, icons
- `docs/`: Product/design docs (`PRD.md`, `DESIGN.md`)
- `tests/`: pytest tests for core flows

## Development & Tests
- Dev server: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- Docker logs: `docker compose logs -f app`
- Stop Docker: `docker compose down`
- Run tests: `PYTHONPATH=. pytest -q`
- Lint/format (optional if installed): `ruff check .`, `black .`

Common routes
- Login: `/login` → Dashboard: `/dashboard`
- Landing: `/c/{public_code}`
- Print: `/print/{public_code}`
- QR PNG: `/qr/{public_code}.png?scale=10&border=2`
- Per‑code notification: `/codes/{id}/notify`

## Packaging
- Distributable archive: `./scripts/package.sh`
  - Default: `dist/MoveCar-<timestamp>-<rev>.tar.gz`
  - Versioned: `./scripts/package.sh v1.0.0` (or `PKG_VERSION=v1.0.0 ./scripts/package.sh`)
  - Excludes local‑only folders (`.git`, `.venv`, `__pycache__`, `data/`, `app/uploads/`, `tests/`, `docs/`)

## Security
- Do not commit `.env` or secrets. Use `.env.example` as a template. Rotate secrets if exposed.
- Run behind HTTPS (Caddy/Nginx). Persist `data/` and `uploads/` on volumes.
- Avoid PII (no phone numbers by default). Scrub logs before sharing.

## Docs & Roadmap
- Product: `docs/PRD.md`
- Design: `docs/DESIGN.md`
- Roadmap: Email/Telegram/NTFY adapters; shared codes (family); expiring/one‑time codes; i18n; PWA; optional WebRTC voice

## Troubleshooting
- “attempt to write a readonly database”: ensure the working directory is writable or set `DB_URL=sqlite:///./data/dev.db`
- First run creates `data/` and `data/uploads/` automatically
- QR via `segno`; PNG via `pypng`
- Bark issues: check base URL reachability, token correctness, outbound connectivity, and HTTP status/text
