# AGENTS.md

Personal fork of `tgbot-collection/ytdlbot`: a Kurigram (pyrogram fork) Telegram
bot that downloads video/audio/files via yt-dlp (+ aria2/requests for direct links).
Russian UI. No test suite.

## Commands
- Install: `pdm install` (preferred) or `pip install -r requirements.txt`
- Run: `python main.py` **from `src/`** — imports are top-level package names
  (`config`, `engine`, `database`), so `cwd` MUST be `src/`. Needs populated `.env`.
- Format: `black .` (no config, no line-length override)
- Regenerate `requirements.txt` from `pyproject.toml`: `python pre-push.py`
  (dependabot uses this; strips version specs to the pinned form). Edit deps in
  `pyproject.toml`, never `requirements.txt` directly.
- Local infra: `docker-compose up -d` (Redis + MySQL; `ytdl` service expects a
  prebuilt `katze-942/ytdlbot` image).

## Setup
- Copy `.env.example` → `.env`. Required: `APP_ID`, `APP_HASH`, `BOT_TOKEN`, `OWNER`.
- `DB_DSN` is read directly via `os.getenv` in `database/model.py` at import time
  (NOT through the `config` layer) — must be set or `create_engine` fails on startup.
  SQLite (`sqlite:///db.sqlite`) or MySQL both work.
- `REDIS_HOST` empty → falls back to `fakeredis` (no Redis needed locally).
- YouTube needs a JS runtime for yt-dlp: install `deno` (bundled in Docker image).
- `config/__init__.py` calls `load_dotenv()` + sets up logging as an import side
  effect — importing anything from `config` loads `.env`.

## Architecture
- `src/main.py`: bot entry. Handlers are **synchronous** (Kurigram runs them across
  `WORKERS` threads). `download_handler` (any private text) is the primary entry.
  The `private_use` decorator gates all handlers: drops non-private messages unless
  they start with `/ytdl`, then enforces the `AUTHORIZED_USER` allowlist.
- `src/engine/__init__.py`: three entrypoints.
  - `youtube_entrance` → `generic.py::YoutubeDownload` — main path for **ALL**
    yt-dlp-supported sites, not just YouTube.
  - `direct_entrance` → `direct.py::DirectDownload` — aria2 (`ENABLE_ARIA2`) or
    requests fallback. `/direct`.
  - `special_download_entrance` → routed by **hostname suffix** via `DOWNLOADER_MAP`
    (pixeldrain / krakenfiles / instagram). `/spdl`. YouTube URLs here raise.
- `src/engine/base.py`: `BaseDownloader` (ABC) is the spine. Subclasses implement
  `_setup_formats`/`_download`/`_start`. `@final start()` drives lifecycle:
  cache lookup (`_get_video_cache`) → hit reuses Telegram `file_id`, miss runs
  `_start()`; per-download tempdir cleaned in `finally`.
- `src/database/`: `cache.py` (Redis db=1, fakeredis fallback; key = md5 of
  url+quality+format+vcodec → stores `file_id`+meta). `model.py` (SQLAlchemy
  `User`/`Setting`, `create_all` auto-creates tables; all access via
  `session_manager()`).
- `src/utils/__init__.py`: `sizeof_fmt`, `timeof_fmt`, `is_youtube`, `debounce`
  (used by progress-bar throttling in `base.py`).

## Quirks
- **yt-dlp is NOT pinned** anymore: `yt-dlp>=2026.6.9` + `yt-dlp-ejs` (JS-runtime
  extractor). Kurigram is pinned (`kurigram==2.2.23`).
- yt-dlp opts in `generic.py`: `source_address: "0.0.0.0"` (forces IPv4);
  `playlist_items: 1` (blocks channel/playlist mass-download). Cookies via
  `BROWSERS` env or `youtube-cookies.txt`; optional `POTOKEN`; proxy from `YT_DLP_PROXY`.
  No default browser cookies — set `BROWSERS` or drop a cookies file if YouTube fails.
- `check_link` (`main.py`) blocks YouTube `channel/` URLs, any URL containing `list`
  (playlists), and `m3u8` unless `M3U8_SUPPORT`.
- Text without `http(s)://` is treated as a **YouTube search query** (`search_ytb`).
- Instagram needs an external service at `http://instagram:15000/?url=...` — a
  separate container NOT defined in this repo's `docker-compose.yml`.
- `.python-version` is `3.14` but Docker uses `python:3.12-alpine`; `requires-python
  >=3.10`. Dockerfile installs `ffmpeg`, `aria2`, `deno`, copies `.venv` libs to the
  system path, and runs `python main.py` from `/app` (no editable install).
- VIP/quota/payments were removed from this fork — do not reintroduce unless asked.
- `CLAUDE.md` has deeper flow notes but its VIP/quota/`Payment`/`engine/helper.py`
  sections are **stale** (that code no longer exists). Trust the code over it.
