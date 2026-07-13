# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Personal fork of [tgbot-collection/ytdlbot](https://github.com/tgbot-collection/ytdlbot):
a Telegram bot that downloads video/audio/files via yt-dlp (and aria2/requests for
direct links). Russian UI, custom format selection, embedded thumbnails/metadata,
IPv4 forcing. `AGENTS.md` is the condensed command/setup/quirks cheat sheet; this file
is the deeper flow reference. Keep both in sync with the code.

## Commands

- Install deps: `pdm install` (preferred) or `pip install -r requirements.txt`
- Run bot: `python main.py` **from `src/`**. Imports are top-level package names
  (`config`, `engine`, `database`), so `cwd` MUST be `src/` — this is also why the
  Dockerfile copies `src` to `/app` and runs there.
- Lint/format: `black .` (no custom config, no line-length override)
- Local infra: `docker-compose up -d` brings up Redis + MySQL (the `ytdl` service
  expects the prebuilt `katze-942/ytdlbot` image).
- Regenerate `requirements.txt` from `pyproject.toml`: `python pre-push.py` (used by
  dependabot; strips version-spec dependencies to the pinned form). Edit deps in
  `pyproject.toml`, never `requirements.txt` directly.

There is **no test suite**. `src/test.py` is a throwaway manual yt-dlp cookie script,
not a real test. Don't write or run tests unless asked.

## Setup essentials

- Copy `.env.example` → `.env`. Required: `APP_ID`, `APP_HASH`, `BOT_TOKEN`, `OWNER`.
  See `.env.example` comments for the rest.
- `REDIS_HOST` empty → falls back to `fakeredis` (no Redis needed for local runs).
- `DB_DSN` is required and read **directly via `os.getenv` in `database/model.py`** at
  import time (NOT through the `config` layer) — it must be set or `create_engine`
  fails on startup. Use SQLite (`sqlite:///db.sqlite`) or MySQL.
- YouTube downloads require a JS runtime for yt-dlp (deno is installed in the Docker
  image; install it locally otherwise).

## Architecture

### Request flow
`src/main.py` is a **Kurigram** (`kurigram`, a pyrogram fork) bot. Handlers are
**synchronous** — Kurigram runs them across `WORKERS` threads. Telegram commands map to
handlers; the catch-all `download_handler` (any incoming private text) is the primary
entry. The `private_use` decorator gates everything: it drops non-private messages
unless they start with `/ytdl`, and enforces the `AUTHORIZED_USER` allowlist.

`download_handler` treats text **without** an `http(s)://` prefix as a YouTube search
query (`search_ytb`, flat `ytsearch` — returns title+url list, no per-result fetch).
With a URL it runs `check_link` then `youtube_entrance`.

The three download entrypoints live in `src/engine/__init__.py`:
- `youtube_entrance` → `YoutubeDownload` (`engine/generic.py`) — the **main path for
  ALL yt-dlp-supported sites**, not just YouTube.
- `direct_entrance` → `DirectDownload` (`engine/direct.py`) — aria2 (`ENABLE_ARIA2`)
  or `requests` fallback. Triggered by `/direct`.
- `special_download_entrance` → routed by **hostname suffix** through `DOWNLOADER_MAP`
  to pixeldrain / krakenfiles / instagram. Triggered by `/spdl`. YouTube URLs here
  raise a "send it directly" error.

### Downloader template (`engine/base.py`)
`BaseDownloader` (ABC) is the spine. Every engine subclasses it and implements
`_setup_formats`, `_download`, `_start`. The `@final start()` method drives the
lifecycle:

```
start() → cache lookup (_get_video_cache)
        → cache hit?  → _upload(file_id, meta)   # reuse Telegram file_id
          cache miss? → _start() → _download() → _upload()
        → finally: tempdir.cleanup()
```

- **Per-download temp dir**: `tempfile.TemporaryDirectory(prefix="ytdl-", dir=TMPFILE_PATH)`
  created in `__init__`, cleaned in `start()`'s `finally` and `__del__`. `main.py` also
  purges leftover contents of `TMPFILE_PATH` (default `/tmp/ytdlbot`) at startup —
  item-by-item, it does not delete the dir itself.
- **Progress UI**: `download_hook`/`upload_hook` render a tqdm-style bar, throttled by
  the `@debounce(5)` decorator on `edit_text` (one Telegram edit per 5s, keyed by
  chat+message id). `download_hook` also aborts if reported size exceeds
  `TG_NORMAL_MAX_SIZE` (2000 MiB). `debounce`, `sizeof_fmt`, `timeof_fmt`, `is_youtube`
  live in `src/utils/__init__.py`.
- **Upload format dispatch** (`_upload` + `send_something`): driven by the user's
  `format` setting (`video`/`audio`/`document`/`photo`). For `video` it tries
  `video → animation → audio → photo` in order until one send succeeds. `get_metadata`
  extracts dimensions/duration via `ffmpeg.probe` and a cover thumbnail via an `ffmpeg`
  subprocess (returns a stub caption if the tempdir is empty).

### Format selection (the fork's core customization)
`YoutubeDownload._setup_formats` + `get_format` (`engine/generic.py`) build a
prioritized list of yt-dlp format strings, joined with `/`. The rules: prefer files
under ~1.5 GB video / ~0.5–1 GB audio, prefer a Russian audio track (`[language=ru]`),
prefer the user's vcodec (default VP9). Postprocessors embed metadata + thumbnail;
audio mode extracts to mp3 (or `AUDIO_FORMAT`). yt-dlp opts of note:
`source_address: "0.0.0.0"` (forces IPv4), `playlist_items: 1` (workaround to stop
channel/playlist links downloading everything), cookies from `BROWSERS` env or
`youtube-cookies.txt` (**no default browser cookies**), optional `POTOKEN`, `proxy`
from `YT_DLP_PROXY`.

### State: cache + database
- **Redis** (`database/cache.py`): db=1, `decode_responses=True`, falls back to
  fakeredis on connection failure. Cache key = `md5(url + quality + format + vcodec)`
  (`_calc_video_key`) → stores the Telegram `file_id` + meta so identical re-requests
  skip downloading.
- **SQLAlchemy** (`database/model.py`): `User` / `Setting` models only,
  `Base.metadata.create_all` auto-creates tables on first connect. All access goes
  through the `session_manager()` context manager (auto commit/rollback/close). User
  settings (quality/format/vcodec) are read fresh from DB on nearly every operation.

### Config (`src/config/`)
- `config.py`: every setting goes through `get_env`, which treats unset **or empty**
  (`VAR=`) as absent, auto-casts `"true"/"false"` → bool and digit strings → int
  (except `AUTHORIZED_USER`). `OWNER` is parsed to a `list[int]`.
- `constant.py`: `BotText` holds all user-facing strings (Russian, HTML parse mode)
  and `Types` holds Kurigram type aliases.
- `config/__init__.py` calls `load_dotenv()` and re-exports `config.config.*` +
  `config.constant.*`, and sets up logging — so importing anything from `config` loads
  `.env` as a side effect.

## Gotchas

- **Disabled link types**: `check_link` (`main.py`) raises on YouTube `channel/` URLs
  and any URL containing `list` (blocks playlists), and rejects `m3u8` unless
  `M3U8_SUPPORT`.
- **Instagram needs an external service**: `engine/instagram.py` calls
  `http://instagram:15000/?url=...` — a separate container not defined in this repo's
  `docker-compose.yml`.
- **yt-dlp is NOT pinned**: `yt-dlp>=2026.6.9` + `yt-dlp-ejs` (JS-runtime extractor)
  in `pyproject.toml`/`requirements.txt`. Kurigram is pinned (`kurigram==2.2.23`).
  Bumping deps requires regenerating `requirements.txt` via `pre-push.py`.
- **VIP / quota / payments were removed** from this fork (no `Payment` model, no
  quota checks, no `/buy`, no APScheduler). `engine/helper.py` was deleted; its
  `debounce` moved to `utils`. Don't reintroduce any of this unless asked.
- `.python-version` is `3.14` but Docker uses `python:3.12-alpine`; `requires-python
  >=3.10`. The Docker build copies `.venv` site-packages into the system path and runs
  `python main.py` from `/app` (the copied `src/`) — no editable install; imports rely
  on `cwd`.
