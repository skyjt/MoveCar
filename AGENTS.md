# Repository Guidelines

## Project Structure & Module Organization
- Root: `PRD.md` (product requirements), `docker-compose.yml`, `.env.example`.
- Backend (planned): `app/` with `main.py`, `routes/`, `services/`, `models.py`, `schemas.py`, `templates/`, `static/`, `uploads/`.
- Docs: `docs/` (e.g., `DESIGN.md`).
- Data: `data/` for SQLite and persistent files (mounted volume).
- Tests: `tests/` mirrors `app/` structure (e.g., `tests/services/test_messages.py`).

## Build, Test, and Development Commands
- Local (dev server): `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Docker (recommended): `docker compose up -d` (start) | `docker compose logs -f app` | `docker compose down`
- Install (when using venv): `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Tests: `pytest -q` (unit tests) | `pytest -q tests/routes -k code`
- Lint/Format (if configured): `ruff check .` | `black .`

## Coding Style & Naming Conventions
- Python: PEP 8, 4‑space indent, 88‑char line length.
- Names: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Structure: thin `routes/`, business logic in `services/`, DB via `models.py` (SQLAlchemy).
- Docs: module/function docstrings for public APIs; user‑visible text in `templates/`.
- 为写完的代码完成详细的注释，注释内容应该以中文为主

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio` for async endpoints.
- Layout: mirror `app/`; name tests as `test_<feature>_*.py`.
- Coverage: target 70%+ for MVP (focus on services and critical routes).
- Examples: `pytest -q tests/services/test_rate_limit.py`.

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (e.g., `feat: add anonymous message endpoint`, `fix: rate limit window`).
- PRs: clear description, scope and rationale; link issues; screenshots for UI; include test plan and risks.
- Requirements: CI green, tests updated, docs updated (PRD/DESIGN if behavior changes), no secrets in diffs.

## Changelog Discipline
- After each user‑requested change that is applied to the repo, update `changelog.md` immediately.
- Record reverse‑chronological entries with: date (YYYY‑MM‑DD), type tags (feat/fix/docs/style/refactor), concise summary, and key files touched.
- Keep entries short and scannable; prefer multiple bullets to a long paragraph.
- 如果用户要求修改，请在完成修改后，务必同步更新 `changelog.md`，确保记录清晰可溯源。

## Security & Configuration Tips
- Do not commit `.env` or secrets; use `.env.example` as a template.
- Run behind HTTPS (Caddy/Nginx). Keep `data/` and `uploads/` on persistent volumes.
- PII: avoid storing phone numbers by default; scrub logs before sharing.
