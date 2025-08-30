2025-08-29
- feat: initialize repository and initial import (local)
- chore: add .gitignore to exclude venv/data/env files

2025-08-29
- docs: add English README as default (README.md)
- docs: add Chinese version (readme_zh.md) and cross-link
- docs: reflect latest routes, Docker flow, and config

2025-08-29
- chore: add remote for GitHub repo skyjt/Move_My_Car; push pending auth

2025-08-29
- docs: link Chinese README from main README; add backlink
2025-08-30 docs: add packaging script and .dockerignore; update README
- Added `scripts/package.sh` to generate tar.gz for releases (excludes local-only files)
- Added `.dockerignore` to keep Docker contexts small
- Updated `README.md` with Packaging instructions
- Key files: `scripts/package.sh`, `.dockerignore`, `README.md`

2025-08-30 fix: apply .env admin password changes; auto-load .env
- `bootstrap_admin` now updates existing admin password when `ADMIN_PASSWORD` changes in `.env`/env
- Auto-load `.env` on startup (via `python-dotenv`) so local runs pick up config without manual export
- Updated `requirements.txt` and README local env guidance
- Key files: `app/database.py`, `requirements.txt`, `README.md`
