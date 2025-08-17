import os
import asyncio
import subprocess
from datetime import timedelta, datetime
import re
from urllib.parse import urlparse
import aiohttp
from pydub import AudioSegment
from utils.config import INTRO_DIR, INTRO_MAX_SECONDS
from utils.logger import bot_logger


def validate_audio_file(path: str, max_seconds: int) -> bool:
    """Check if the audio file is valid and within duration limit."""
    try:
        audio = AudioSegment.from_file(path)
        return len(audio) / 1000 <= max_seconds
    except Exception as e:
        bot_logger.error(f"Errore validazione file audio {path}: {e}")
        return False
    
def is_valid_youtube_url(url: str) -> bool:
    """Check if the URL is a valid YouTube URL."""
    parsed = urlparse(url)
    return parsed.netloc in ('www.youtube.com', 'youtu.be')

def validate_time_format(time_str: str) -> bool:
    """Validate time format (HH:MM:SS or MM:SS)."""
    pattern = r'^(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})$'
    return bool(re.match(pattern, time_str))

async def download_audio_clip(user_id, guild_id, url: str, start_time: str, end_time: str) -> bool:
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
    
    
    if not validate_time_format(start_time):
        bot_logger.error("start_time deve essere nel formato HH:MM:SS o MM:SS")
        return False
    if not validate_time_format(end_time):
        bot_logger.error("end_time deve essere nel formato HH:MM:SS o MM:SS")
        return False
    
    try:
        if validate_time_format(start_time):
            try:
                start_dt = datetime.strptime(start_time, "%H:%M:%S")
            except ValueError:
                start_dt = datetime.strptime(f"00:{start_time}", "%H:%M:%S")
        else:
            bot_logger.error("start_time deve essere nel formato HH:MM:SS o MM:SS")
            return False
        if validate_time_format(end_time):
            try:
                end_dt = datetime.strptime(end_time, "%H:%M:%S")
            except ValueError:
                end_dt = datetime.strptime(f"00:{end_time}", "%H:%M:%S")
        else:
            bot_logger.error("end_time deve essere nel formato HH:MM:SS o MM:SS")
            return False

        start_td = timedelta(hours=start_dt.hour, minutes=start_dt.minute, seconds=start_dt.second)
        end_td = timedelta(hours=end_dt.hour, minutes=end_dt.minute, seconds=end_dt.second)

        duration = (end_td - start_td).total_seconds()

        if duration > INTRO_MAX_SECONDS:
            end_td = start_td + timedelta(seconds=INTRO_MAX_SECONDS)
            end_time = str(timedelta(seconds=int(end_td.total_seconds()))).split('.')[0]

    except ValueError:
        bot_logger.error("start_time e end_time devono essere nel formato HH:MM:SS")
        return False
    
    if not is_valid_youtube_url(url):
        bot_logger.error("URL non valido. Deve essere un link YouTube.")
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

        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            if validate_audio_file(path, INTRO_MAX_SECONDS):
                bot_logger.info(f"Download completato: {stdout.decode()}")
                return True

            bot_logger.error(f"File audio {path} non valido o troppo lungo")
            # os.remove(path)  # Rimuovi il file non valido
            return False

        bot_logger.error(f"Errore durante il download: {stderr.decode()}")
        return False

        # result = subprocess.run(command, check=True, capture_output=True, text=True)
        # bot_logger.info("Download completato:", result.stdout)
        #return True
    except Exception as e:
        bot_logger.error(f"Errore durante il download: {e}")
        return False



async def save_intro_file(file, user_id, guild_id):
    if not file.content_type.startswith('audio/') or not file.filename.endswith('.mp3'):
        bot_logger.error(f"File non supportato per utente {user_id} in server {guild_id}")
        return False

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
