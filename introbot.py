import asyncio
import sys
from typing import Any

import discord
from discord.ext import commands

from services.voice_handler import play_intro_if_available
from utils.config import DISCORD_BOT_TOKEN
from utils.logger import bot_logger

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

reconnect_attempts = 0
MAX_RECONNECT_ATTEMPTS = 5


async def monitor_connection() -> None:
    # discord.py gestisce la riconnessione automaticamente; questo task
    # si limita a chiudere il bot se le disconnessioni superano il limite.
    while True:
        await asyncio.sleep(5)
        if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
            bot_logger.error("--- Numero massimo di tentativi di riconnessione raggiunto, arresto del bot")
            await bot.close()
            break


class IntroBot(commands.Bot):
    async def setup_hook(self) -> None:
        asyncio.create_task(monitor_connection())
        await self.load_extension("cogs.intro_manager")
        try:
            synced = await self.tree.sync()
            bot_logger.info(f"Comandi slash sincronizzati: {len(synced)}")
        except Exception as e:
            bot_logger.error(f"Errore durante la sincronizzazione dei comandi: {e}")


bot = IntroBot(command_prefix=[], intents=intents)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    await play_intro_if_available(member, before, after)


@bot.event
async def on_error(event: str, *args: Any, **kwargs: Any) -> None:
    exc_type, exc_value, exc_tb = sys.exc_info()
    if exc_value is not None:
        bot_logger.error(f"Errore nell'evento {event}", exc_info=True)
        if "WebSocket closed with 4006" in str(exc_value):
            bot_logger.warning("--- Possibile invalidazione della sessione WebSocket rilevata")
    else:
        bot_logger.error(f"Errore nell'evento {event}: args={args}")


@bot.event
async def on_disconnect() -> None:
    global reconnect_attempts
    bot_logger.warning("--- Disconnessione dal WebSocket rilevata")
    reconnect_attempts += 1


@bot.event
async def on_ready() -> None:
    global reconnect_attempts
    bot_logger.info(f"--- Bot connesso come {bot.user}")
    if reconnect_attempts > 0:
        bot_logger.info(f"--- Riconnessione riuscita dopo {reconnect_attempts} tentativi")
    reconnect_attempts = 0


async def main() -> None:
    await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
