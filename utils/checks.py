from discord import Interaction
from discord.app_commands import check

def is_guild_context():
    @check
    async def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message(
                "⛔ Questo comando può essere usato solo in un canale del server.",
                ephemeral=True
            )
            return False
        return True
    return predicate
