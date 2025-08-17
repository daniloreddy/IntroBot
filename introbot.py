import asyncio
import discord
from discord.ext import commands
from utils.config import DISCORD_BOT_TOKEN
from utils.logger import bot_logger
from services.voice_handler import play_intro_if_available

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=None, intents=intents)

# Listener vocale
@bot.event
async def on_voice_state_update(member, before, after):
    await play_intro_if_available(bot, member, before, after)


async def main():
    await bot.load_extension("cogs.intro_manager")
    await bot.start(DISCORD_BOT_TOKEN)
    try:
        synced = await bot.tree.sync()
        bot_logger.info(f"Comandi slash sincronizzati: {len(synced)}")
    except Exception as e:
        bot_logger.error(f"Errore durante la sincronizzazione dei comandi: {e}")

if __name__ == "__main__":
    asyncio.run(main())
