import asyncio
import os
from typing import cast

import discord

from utils.config import FFMPEG_PATH, INTRO_MAX_SECONDS
from utils.file_utils import get_intro_path, validate_audio_file
from utils.logger import bot_logger

guild_queues: dict[int, asyncio.Queue[discord.Member]] = {}
guild_tasks: dict[int, asyncio.Task[None]] = {}


async def guild_player(guild_id: int, queue: asyncio.Queue[discord.Member]) -> None:
    while True:
        member = await queue.get()

        # Re-check member is still in a voice channel (may have left while queued)
        if member.voice is None or member.voice.channel is None:
            bot_logger.debug(f"--- {member.name} ha lasciato il canale prima della riproduzione, skip")
            queue.task_done()
            continue

        target_channel = member.voice.channel
        path = get_intro_path(member.id, guild_id)

        if not os.path.exists(path):
            bot_logger.debug(f"--- Nessun intro per {member.name}, skip")
            queue.task_done()
            continue

        if not await validate_audio_file(path, INTRO_MAX_SECONDS):
            bot_logger.debug(f"--- File intro non valido per {member.name}, skip")
            queue.task_done()
            continue

        vc: discord.VoiceClient | None = None
        try:
            voice_client = cast(discord.VoiceClient | None, target_channel.guild.voice_client)

            if voice_client and voice_client.is_connected():
                if voice_client.channel != target_channel:
                    await voice_client.move_to(target_channel)
                vc = voice_client
            else:
                max_retries = 2
                for attempt in range(max_retries + 1):
                    try:
                        vc = cast(discord.VoiceClient, await target_channel.connect(reconnect=False))
                        for _ in range(6):
                            if vc.is_connected():
                                break
                            await asyncio.sleep(0.5)
                        else:
                            raise discord.DiscordException("Connection timeout")
                        break
                    except discord.DiscordException as e:
                        bot_logger.error(f"--- Tentativo {attempt + 1}/{max_retries + 1} fallito: {e}")
                        if attempt == max_retries:
                            raise
                        await asyncio.sleep(1)

            assert vc is not None
            vc.play(discord.FFmpegPCMAudio(path, executable=FFMPEG_PATH, before_options=f"-t {INTRO_MAX_SECONDS} -loglevel panic"))
            bot_logger.debug(f"--- Riproduzione avviata per {member.name}")

            timeout: float = 0
            max_timeout = INTRO_MAX_SECONDS + 2
            while vc.is_playing() and timeout < max_timeout:
                await asyncio.sleep(0.5)
                timeout += 0.5

            bot_logger.debug(f"--- Riproduzione terminata per {member.name}")

        except discord.DiscordException as e:
            bot_logger.error(f"Errore Discord durante la riproduzione per {member.name}: {e}")
        except OSError as e:
            bot_logger.error(f"Errore accesso file audio per {member.name}: {e}")
        finally:
            if vc and vc.is_connected():
                await vc.disconnect()
                bot_logger.debug("--- Disconnesso dal canale vocale")
            queue.task_done()


async def play_intro_if_available(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    bot_logger.debug(f"--- {member.name} Passa da canale {before.channel} a canale {after.channel}")

    if member.bot or before.channel == after.channel or after.channel is None:
        return

    guild_id = after.channel.guild.id

    # Enqueue member (check intro exists early to avoid filling queue with no-ops)
    path = get_intro_path(member.id, guild_id)
    if not os.path.exists(path):
        return

    q = guild_queues.setdefault(guild_id, asyncio.Queue())

    # Start consumer task if not running (check is synchronous — no await between check and create_task)
    if guild_id not in guild_tasks or guild_tasks[guild_id].done():
        guild_tasks[guild_id] = asyncio.create_task(guild_player(guild_id, q))

    q.put_nowait(member)
    bot_logger.debug(f"--- {member.name} aggiunto alla coda (guild {guild_id}, size={q.qsize()})")
