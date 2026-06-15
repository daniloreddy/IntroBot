import asyncio
import os
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

import aiohttp

from utils.config import FFMPEG_DIR, FFPROBE_PATH, INTRO_DIR, INTRO_MAX_SECONDS
from utils.logger import bot_logger


async def validate_audio_file(path: str, max_seconds: int) -> bool:
    # pydub.from_file() chiama get_prober_name() che usa shutil.which() ignorando
    # qualsiasi path configurato manualmente. Usiamo ffprobe direttamente.
    try:
        process = await asyncio.create_subprocess_exec(
            FFPROBE_PATH,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
        except asyncio.TimeoutError:
            process.kill()
            bot_logger.error(f"Timeout ffprobe su {path}")
            return False
        if process.returncode != 0:
            bot_logger.error(f"ffprobe errore su {path}: {stderr.decode().strip()}")
            return False
        duration = float(stdout.decode().strip())
        return duration <= max_seconds
    except Exception as e:
        bot_logger.error(f"Errore validazione file audio {path}: {e}")
        return False


def is_valid_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in ("www.youtube.com", "youtu.be")


def validate_time_format(time_str: str) -> bool:
    pattern = r"^(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})$"
    return bool(re.match(pattern, time_str))


async def download_audio_clip(user_id: int, guild_id: int, url: str, start_time: str, end_time: str) -> bool:
    guild_dir = os.path.join(INTRO_DIR, str(guild_id))
    os.makedirs(guild_dir, exist_ok=True)
    path = os.path.join(guild_dir, f"{user_id}.mp3")

    # FIX: validazione singola; rimossi i blocchi doppi irraggiungibili
    if not validate_time_format(start_time):
        bot_logger.error("start_time deve essere nel formato HH:MM:SS o MM:SS")
        return False
    if not validate_time_format(end_time):
        bot_logger.error("end_time deve essere nel formato HH:MM:SS o MM:SS")
        return False
    if not is_valid_youtube_url(url):
        bot_logger.error("URL non valido. Deve essere un link YouTube.")
        return False

    try:
        try:
            start_dt = datetime.strptime(start_time, "%H:%M:%S")
        except ValueError:
            start_dt = datetime.strptime(f"00:{start_time}", "%H:%M:%S")
        try:
            end_dt = datetime.strptime(end_time, "%H:%M:%S")
        except ValueError:
            end_dt = datetime.strptime(f"00:{end_time}", "%H:%M:%S")

        start_td = timedelta(hours=start_dt.hour, minutes=start_dt.minute, seconds=start_dt.second)
        end_td = timedelta(hours=end_dt.hour, minutes=end_dt.minute, seconds=end_dt.second)

        duration = (end_td - start_td).total_seconds()
        if duration <= 0:
            bot_logger.error("end_time deve essere successivo a start_time")
            return False
        if duration > INTRO_MAX_SECONDS:
            end_td = start_td + timedelta(seconds=INTRO_MAX_SECONDS)
            end_time = str(timedelta(seconds=int(end_td.total_seconds()))).split(".")[0]

    except ValueError:
        bot_logger.error("start_time e end_time devono essere nel formato HH:MM:SS")
        return False

    command = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "--ffmpeg-location",
        FFMPEG_DIR,
        "--postprocessor-args",
        f"ffmpeg:-ss {start_time} -to {end_time}",
        "-o",
        path,
        url,
    ]

    try:
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        # FIX: aggiunto timeout per evitare hang su URL lenti o bloccati
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
        except asyncio.TimeoutError:
            process.kill()
            bot_logger.error("Timeout durante il download con yt-dlp")
            return False

        if process.returncode == 0:
            if await validate_audio_file(path, INTRO_MAX_SECONDS):
                bot_logger.info(f"Download completato: {stdout.decode()}")
                return True
            bot_logger.error(f"File audio {path} non valido o troppo lungo")
            return False

        bot_logger.error(f"Errore durante il download: {stderr.decode()}")
        return False

    except Exception as e:
        bot_logger.error(f"Errore durante il download: {e}")
        return False


async def save_intro_file(file: object, user_id: int, guild_id: int, temp: bool = False) -> bool:
    if not file.content_type.startswith("audio/") or not file.filename.lower().endswith(".mp3"):  # type: ignore[attr-defined]
        bot_logger.error(f"File non supportato per utente {user_id} in server {guild_id}")
        return False

    guild_dir = os.path.join(INTRO_DIR, str(guild_id))
    os.makedirs(guild_dir, exist_ok=True)
    path = get_intro_path(user_id, guild_id, temp=temp)

    # FIX: aggiunto timeout sulla richiesta HTTP
    timeout = aiohttp.ClientTimeout(total=30)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(file.url) as resp:  # type: ignore[attr-defined]
                if resp.status == 200:
                    with open(path, "wb") as f:
                        f.write(await resp.read())
                    bot_logger.info(f"File intro salvato per utente {user_id} in server {guild_id}")
                    return True
    except Exception as e:
        bot_logger.error(f"Errore salvataggio file intro per utente {user_id} in server {guild_id}: {e}")
    return False


def delete_intro_file(user_id: int, guild_id: int) -> bool:
    path = get_intro_path(user_id, guild_id)
    if os.path.exists(path):
        os.remove(path)
        bot_logger.info(f"File intro cancellato per utente {user_id} in server {guild_id}")
        return True
    return False


def get_intro_path(user_id: int, guild_id: int, temp: bool = False) -> str:
    filename = f"{user_id}.tmp.mp3" if temp else f"{user_id}.mp3"
    return os.path.join(INTRO_DIR, str(guild_id), filename)
