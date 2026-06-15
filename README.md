# IntroBot

Discord bot that plays a personal audio intro when a user joins a voice channel. Each user per guild has one `.mp3` intro (max 11 seconds). When they join a voice channel, the bot connects and plays it automatically.

## Features

- **Auto-play** — bot joins and plays your intro every time you enter a voice channel
- **Per-guild queue** — if multiple users join simultaneously, intros play in order; different guilds play in parallel
- **YouTube clip** — cut any YouTube video to your intro with `/intro-youtube`
- **Direct upload** — upload an `.mp3` file directly with `/intro-upload`
- **Guild-only** — all commands work only inside a server, never in DMs

## Requirements

- Python 3.11+
- FFmpeg (+ ffprobe) on `PATH`, or configured via `.env`
- A Discord bot token with the following enabled in the [Developer Portal](https://discord.com/developers/applications):
  - Privileged intent: **Server Members**
  - Privileged intent: **Message Content** (optional, no prefix commands)
  - Bot permission: **Connect** + **Speak** in voice channels

## Setup

```bash
git clone <repo>
cd IntroBot
cp .env.example .env        # fill in DISCORD_BOT_TOKEN
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Run

```bash
scripts/introbot.sh         # Linux / macOS
scripts\introbot.bat        # Windows
```

The scripts auto-create and activate the venv if it doesn't exist.

### Docker

```bash
cp .env.example .env        # fill in DISCORD_BOT_TOKEN
docker compose up -d
```

Audio files are persisted in `./data`, logs in `./logs` (both mounted as volumes).

## Configuration

Copy `.env.example` to `.env` and set the values:

| Variable | Required | Default | Description |
|---|---|---|---|
| `DISCORD_BOT_TOKEN` | ✅ | — | Bot token from Discord Developer Portal |
| `DISCORD_FALLBACK_ID` | | `123456789012345678` | Owner Discord user ID |
| `LOG_LEVEL` | | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `FFMPEG_PATH` | | `ffmpeg` | Full path to ffmpeg binary |
| `FFPROBE_PATH` | | auto-derived from `FFMPEG_PATH` | Full path to ffprobe binary |

## Slash Commands

| Command | Description |
|---|---|
| `/intro-youtube` | Download a clip from YouTube as your intro |
| `/intro-upload` | Upload an `.mp3` file directly |
| `/intro-delete` | Delete your current intro |
| `/intro-info` | Show size and creation date of your intro |
| `/intro-play` | Manually trigger your intro in the current voice channel |
| `/intro_set_volume` | *(not yet implemented)* |

## Architecture

```
introbot.py          — entry point; bot subclass, event handlers, reconnect monitor
cogs/
  intro_manager.py   — all slash commands
services/
  voice_handler.py   — per-guild queue + consumer tasks; plays intros on voice join
utils/
  config.py          — env vars, path constants
  file_utils.py      — file I/O, yt-dlp download, ffprobe validation
  checks.py          — is_guild_context() decorator
  logger.py          — rotating file loggers
data/intros/         — <guild_id>/<user_id>.mp3
logs/                — bot.log, services.log, errors.log
```

## Development

```bash
scripts/check.sh     # ruff lint + format check + mypy + pytest
```
