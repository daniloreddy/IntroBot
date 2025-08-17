import os
import asyncio
import discord

from utils.file_utils import get_intro_path, validate_audio_file
from utils.logger import bot_logger
from utils.config import INTRO_MAX_SECONDS


# Lock per ogni utente+server
play_locks = {}

# Flag per evitare riproduzioni concorrenti nello stesso server
bot_busy = set()


async def play_intro_if_available(_, member, before, after):
    bot_logger.debug(f"--- {member.name} Passa da canale {before.channel} a canale {after.channel}")

    if member.bot or before.channel == after.channel or after.channel is None:
        return

    key_lock = f"{member.id}-{after.channel.guild.id}"
    key_busy = f"{after.channel.guild.id}"

    # Skip se il bot è già impegnato in questo server
    if key_busy in bot_busy:
        bot_logger.debug(f"--- Bot già impegnato nel server {key_busy}, ignora evento")
        return

    lock = play_locks.setdefault(key_lock, asyncio.Lock())

    async with lock:
        voice_client = after.channel.guild.voice_client
        if voice_client and voice_client.is_connected():
            if voice_client.channel != after.channel:
                await voice_client.move_to(after.channel)
            if voice_client.is_playing():
                bot_logger.debug("--- Voice client già in riproduzione, ignoro")
                return

        path = get_intro_path(member.id, after.channel.guild.id)
        if not os.path.exists(path) or not validate_audio_file(path, INTRO_MAX_SECONDS):
            bot_logger.debug("--- File intro non esiste per l'utente, ignoro")
            return

        try:
            bot_busy.add(key_busy)

            vc = await after.channel.connect(reconnect=True)
            bot_logger.debug("--- Connessione vocale richiesta, attendo stabilizzazione...")

            # Aspetta max 3 secondi
            for _ in range(6):
                if vc.is_connected():
                    break
                await asyncio.sleep(0.5)
            else:
                bot_logger.error(f"Timeout di connessione vocale per {member.name} nel server {after.channel.guild.id}")
                bot_busy.discard(key_busy)
                return

            bot_logger.debug("--- Connessione stabilita, avvio riproduzione")
            vc.play(discord.FFmpegPCMAudio(path, before_options=f"-t {INTRO_MAX_SECONDS} -loglevel panic"))
            bot_logger.debug("--- Audio avviato")

            # Verifica playback
            await asyncio.sleep(0.5)
            bot_logger.debug(f"vc.is_connected() = {vc.is_connected()}, vc.is_playing() = {vc.is_playing()}")

            timeout = 0
            max_timeout = INTRO_MAX_SECONDS + 2  # Margine di 2 secondi
            while vc.is_playing() and timeout < max_timeout:
                await asyncio.sleep(0.5)
                timeout += 0.5

            bot_logger.debug("--- Riproduzione terminata o timeout")
            await vc.disconnect()
            # await asyncio.sleep(0.5)
            bot_logger.debug("--- Disconnesso dal canale vocale")

        except discord.DiscordException as e:
            bot_logger.error(f"Errore Discord durante la riproduzione per {member.name}: {e}")
        except OSError as e:
            bot_logger.error(f"Errore di accesso al file audio per {member.name}: {e}")
        finally:
            bot_busy.discard(key_busy)
            play_locks.pop(key_lock, None)
