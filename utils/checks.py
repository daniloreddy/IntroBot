from typing import Callable, TypeVar

from discord import Interaction
from discord.app_commands import check

from utils.logger import bot_logger

T = TypeVar("T")


def is_guild_context() -> Callable[[T], T]:
    @check
    async def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            command_name = interaction.command.name if interaction.command else "sconosciuto"
            bot_logger.warning(f"Tentativo di usare comando {command_name} fuori da un server da parte di {interaction.user.id}")
            await interaction.response.send_message("⛔ Questo comando può essere usato solo in un canale del server.", ephemeral=True)
            return False
        return True

    return predicate
