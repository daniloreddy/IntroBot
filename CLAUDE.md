# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Discord bot that plays a personal audio intro when a user joins a voice channel. Each user per guild can have one `.mp3` intro stored under `data/intros/<guild_id>/<user_id>.mp3`.

## Commands

**Run the bot:**
```bat
scripts\introbot.bat          # Windows
./scripts/introbot.sh         # Linux (also used by the systemd service)
```

**Lint / format / type-check:**
```bash
scripts/check.sh              # ruff lint, ruff format, mypy, pytest
.venv/bin/ruff check .
.venv/bin/ruff format .
.venv/bin/mypy introbot.py cogs/ services/ utils/
```

No test suite exists yet (`tests/` not present).

## Environment

Requires a `.env` file (never read or log it). See `.env.example` for all variables.
- `DISCORD_BOT_TOKEN` — required; bot refuses to start without it
- `FFMPEG_PATH` — optional; defaults to `ffmpeg` on PATH
- `FFPROBE_PATH` — optional; auto-derived from same directory as `FFMPEG_PATH`
- `LOG_LEVEL` — optional; defaults to `INFO`

FFmpeg and ffprobe must be available (on PATH or via env vars). Venv lives in `.venv/`.

## Architecture

```
introbot.py          — entry point; IntroBot subclass, event handlers, reconnect monitor
cogs/
  intro_manager.py   — all slash commands (/intro-upload, /intro-youtube,
                        /intro-delete, /intro-info, /intro-play, /intro_set_volume)
services/
  voice_handler.py   — on_voice_state_update logic; per-guild queue + consumer tasks
utils/
  config.py          — env vars, path constants, INTRO_MAX_SECONDS (11s)
  file_utils.py      — file I/O, yt-dlp download, ffprobe validation
  checks.py          — is_guild_context() app_commands check decorator
  logger.py          — rotating loggers: bot.log, services.log, errors.log
data/intros/         — runtime audio storage, gitignored
logs/                — gitignored
```

**Data flow on voice join:** `on_voice_state_update` → `play_intro_if_available` in `voice_handler.py`.

**Concurrency model:** Per-guild `asyncio.Queue[discord.Member]` + a long-lived consumer task per guild (`guild_player`). The producer (`play_intro_if_available`) enqueues the member if their intro file exists; the consumer connects, plays, disconnects, then loops on `await queue.get()`. The task is created lazily on first enqueue and runs indefinitely. Different guilds have independent queues and run in parallel. Discord limits a bot to one `VoiceClient` per guild, so within a guild playback is always sequential.

**Audio validation:** `validate_audio_file` uses `ffprobe` directly via `asyncio.create_subprocess_exec` with a 10s timeout. pydub is not used anywhere.

**Slash commands** are registered via `bot.tree.sync()` in `setup_hook` at startup.

**Reconnect logic:** `monitor_connection()` task in `introbot.py` shuts the bot down after `MAX_RECONNECT_ATTEMPTS` (5) disconnects. discord.py handles reconnection automatically.

## Key Constraints

- `INTRO_MAX_SECONDS = 11` — enforced at upload/download time (ffprobe check) and at playback time (`-t` flag passed to FFmpeg).
- Only `.mp3` is stored; yt-dlp always outputs mp3; `save_intro_file` enforces `.mp3`; `/intro-upload` rejects non-mp3 at the command level too.
- Commands are guild-only; `is_guild_context()` guard rejects DM usage.
- Upload uses a temp file (`{user_id}.tmp.mp3`) → validate → `os.replace()` to avoid destroying the existing intro on a failed upload.
- `discord.py >= 2.5` requires both `PyNaCl` and `davey` for voice support. Both are in `requirements.txt`.
- `guild_tasks[guild_id].done()` check before `create_task` is synchronous (no `await` between check and task creation), making it race-free without a lock.
