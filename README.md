# Move My Car (self-hosted, privacy-friendly)

[中文文档 / Chinese README](readme_zh.md)

An open-source, self-hosted “move my car” QR code tool. It lets visitors contact the car owner anonymously without exposing a phone number. The MVP focuses on: code management, anonymous messages (text + image), lightweight notifications, basic abuse protection, and printable/online QR codes.

## Tech Stack
- python
- html
- **codex cli**（https://github.com/openai/codex）

## Quick Start
- Docker (recommended)
  - Copy config: `cp .env.example .env`
  - Start: `docker compose up -d`
  - Open: `http://localhost:8000/login` (default admin `admin/admin`)
- Local (without Docker)
  - Create venv: `python -m venv .venv && source .venv/bin/activate`
  - Install deps: `pip install -r requirements.txt`
  - Env file: `cp .env.example .env` (the app auto-loads `.env` via python-dotenv)
  - Run dev server: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
  - Open: `http://127.0.0.1:8000/login`

## What You Can Do
- Create and manage multiple move-codes (activate/pause/delete, display name).
- Print or download a QR code PNG for each code.
- Let visitors scan `/c/{public_code}` and leave a message (text + optional image ≤ 5 MB).
- Review messages on the dashboard and mark “processed”.
- Optional push notification per code via Bark.
- Built-in rate limiting and per-code blacklist to reduce abuse.

## Notifications (Bark)
- Per-code settings: Dashboard → target code → “Notification”.
- Channels:
  - None (default): no external push.
  - Bark: follow https://bark.day.app/#/tutorial to obtain a device token.
- Configure Bark:
  - Base URL: default `https://api.day.app`.
  - Token: paste your Bark device token.
  - Send a “Test Notification” after saving to verify.
- When enabled, a successful submission on the landing page triggers a push with a short preview and a dashboard link.

## Configuration (.env)
- `APP_SECRET`: Session signing key (change in production).
- `APP_BASE_URL`: Public base URL used in printable pages and QR links.
- `DB_URL`: Database URL; defaults to `sqlite:///data/app.db`.
- `DATA_DIR`: Data folder for DB and uploads; defaults to `./data`.
- `MAX_IMAGE_MB`: Upload image limit (default 5).
- `RATE_LIMIT_WINDOW` / `RATE_LIMIT_COUNT`: Rate limit window and quota (default 60s / 1).
- `ANON_CHAT_ENABLED`: Whether to enable real-time chat (MVP uses simple message, default false).
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`: Default admin bootstrap.

Notes:
- SQLite DB is stored under `data/` and images under `data/uploads/`.
- Docker Compose maps `./data` as a volume so the DB and uploads persist.

## Project Structure
- `app/`: FastAPI backend and Jinja2 templates.
- `app/routes/`: Page and API routes; `services/`: rate limiting, notifications, etc.
- `app/templates/`: HTML templates; `app/style.css`, `app/icon.svg` for UI.
- `docs/`: Documentation (`DESIGN.md`, `PRD.md`).
- `tests/`: pytest tests for critical routes and services.

## Development & Tests
- Dev server: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- Docker logs: `docker compose logs -f app`
- Stop Docker: `docker compose down`
- Run tests: `pytest -q`
- Useful routes:
  - Login: `/login` → Dashboard: `/dashboard`
  - Landing: `/c/{public_code}`
  - Print: `/print/{public_code}` (download button included)
  - QR PNG: `/qr/{public_code}.png?scale=10&border=2`
  - Per-code notification page: `/codes/{id}/notify`

## Packaging
- Create a distributable archive: `./scripts/package.sh`
  - Default: `dist/MoveCar-<timestamp>-<rev>.tar.gz`
  - With version: `./scripts/package.sh v1.0.0` (or `PKG_VERSION=v1.0.0 ./scripts/package.sh`)
  - Excludes local-only files like `.git`, `.venv`, `__pycache__`, `data/`, `app/uploads/`, `tests/`, and `docs/` for smaller runtime delivery.

## Docs & Roadmap
- Product: `docs/PRD.md`
- Design: `docs/DESIGN.md`
- Roadmap (next): email/Telegram/NTFY adapters, shared codes (family), expiring/one-time codes, i18n, PWA, optional WebRTC voice.

## Tips & Troubleshooting
- “attempt to write a readonly database”: ensure the working directory is writable or set `DB_URL=sqlite:///./data/dev.db`.
- On first run, the app creates `data/` and `data/uploads/` automatically.
- QR generation uses `segno`; PNG writing uses `pypng`.
- For production, enable HTTPS (via Caddy/Nginx), change `APP_SECRET` and the default admin password, and persist `data/`.
- Bark issues: check base URL reachability, token correctness, outbound connectivity, and returned HTTP status.
