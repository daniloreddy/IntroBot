import os
import subprocess
import datetime
from datetime import timedelta, datetime
import aiohttp
from utils.config import INTRO_DIR, INTRO_MAX_SECONDS
from utils.logger import bot_logger


def download_audio_clip(user_id, guild_id, url: str, start_time: str, end_time: str) -> bool:
    """
    Scarica una clip audio da YouTube usando yt-dlp e FFmpeg, limitando la durata a INTRO_MAX_SECONDS.

    Args:
        url (str): URL del video YouTube
        start_time (str): tempo di inizio in formato HH:MM:SS
        end_time (str): tempo di fine richiesto in formato HH:MM:SS

    Returns:
        bool: True se completato con successo, False in caso di errore
    """
    
    guild_dir = os.path.join(INTRO_DIR, str(guild_id))
    os.makedirs(guild_dir, exist_ok=True)
    path = os.path.join(guild_dir, f"{user_id}.mp3")
    
    try:
        start_dt = datetime.strptime(start_time, "%H:%M:%S")
        end_dt = datetime.strptime(end_time, "%H:%M:%S")

        start_td = timedelta(hours=start_dt.hour, minutes=start_dt.minute, seconds=start_dt.second)
        end_td = timedelta(hours=end_dt.hour, minutes=end_dt.minute, seconds=end_dt.second)

        duration = (end_td - start_td).total_seconds()

        if duration > INTRO_MAX_SECONDS:
            end_td = start_td + timedelta(seconds=INTRO_MAX_SECONDS)
            end_time = str(end_td)

    except ValueError:
        bot_logger.error("start_time e end_time devono essere nel formato HH:MM:SS")
        return False

    command = [
        "yt-dlp",
        "-k",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--postprocessor-args", f"-ss {start_time} -to {end_time}",
        "-o", path,
        url
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        bot_logger.info("Download completato:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        bot_logger.error("Errore durante il download:", e.stderr)
        return False

async def save_intro_file(file, user_id, guild_id):
    guild_dir = os.path.join(INTRO_DIR, str(guild_id))
    os.makedirs(guild_dir, exist_ok=True)
    path = os.path.join(guild_dir, f"{user_id}.mp3")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file.url) as resp:
                if resp.status == 200:
                    with open(path, "wb") as f:
                        f.write(await resp.read())
                    bot_logger.info(f"File intro salvato per utente {user_id} in server {guild_id}")
                    return True
    except Exception as e:
        bot_logger.error(f"Errore salvataggio file intro per utente {user_id} in server {guild_id}: {e}")
    return False

def delete_intro_file(user_id, guild_id):
    path = os.path.join(INTRO_DIR, str(guild_id), f"{user_id}.mp3")
    if os.path.exists(path):
        os.remove(path)
        bot_logger.info(f"File intro cancellato per utente {user_id} in server {guild_id}")
        return True
    return False

def get_intro_path(user_id, guild_id):
    return os.path.join(INTRO_DIR, str(guild_id), f"{user_id}.mp3")
