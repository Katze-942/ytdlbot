# AGENTS.md

## Commands
- Install deps: `pdm install` (preferred) or `pip install -r requirements.txt`
- Activate venv: `source .venv/bin/activate`
- Run bot: `python src/main.py` (requires `.env`)
- Lint: `black .` (no custom config)

## Setup
- Copy `.env.example` to `.env`, fill required vars: `APP_ID`, `APP_HASH`, `BOT_TOKEN`, `OWNER`
- Redis: leave `REDIS_HOST` empty (uses fakeredis) or set to Redis host
- MySQL: set `DB_DSN` (e.g., `mysql+pymysql://user:pass@mysql/dbname`)
- Or use `docker-compose up -d` for Redis/MySQL services
- yt-dlp requires deno (JS runtime) for YouTube: install deno, or use Docker image (includes deno)

## Architecture
- Entry point: `src/main.py`
- `src/engine/`: Download handlers for YouTube, Instagram, Pixeldrain, KrakenFiles, direct links
- `src/config/config.py`: All env vars loaded via `get_env` helper
- `src/database/`: User quota, settings, Redis/MySQL models

## Quirks
- yt-dlp pinned to `2026.3.17` (pyproject.toml/requirements.txt)
- Uses `kurigram==2.2.18` (pyrogram fork) as Telegram client
- Dockerfile (python:3.12-alpine) explicitly installs ffmpeg, aria2, deno
- No test suite
- Forces IPv4 via yt-dlp `source_address: 0.0.0.0` (src/engine/generic.py:90)
- `BROWSERS` env: set to browser name (e.g., `firefox`) for yt-dlp cookies
- `POTOKEN` env: required for YouTube in some cases (see yt-dlp PO Token guide)
- Playlist downloads disabled: `playlist_items: 1` set in yt-dlp options (src/engine/generic.py:99)
