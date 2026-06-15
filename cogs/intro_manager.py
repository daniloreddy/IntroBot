import asyncio
import os
from datetime import datetime
from typing import cast

import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import is_guild_context
from utils.config import FFMPEG_PATH, INTRO_MAX_SECONDS
from utils.file_utils import delete_intro_file, download_audio_clip, get_intro_path, save_intro_file, validate_audio_file, validate_time_format


class IntroManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="intro_set_volume", description="Imposta il volume di riproduzione della tua intro (0.0 a 1.0)")
    @app_commands.describe(volume="Il livello del volume (es. 0.5 per metà volume)")
    @is_guild_context()
    async def set_volume(self, interaction: discord.Interaction, volume: float) -> None:
        await interaction.response.send_message("⚠️ Funzione non ancora implementata.", ephemeral=True)

    @app_commands.command(name="intro-upload", description="Carica o sovrascrivi il tuo file intro (.mp3)")
    @is_guild_context()
    async def upload_intro(self, interaction: discord.Interaction, file: discord.Attachment) -> None:
        if not file.filename.lower().endswith(".mp3"):
            await interaction.response.send_message("❌ Solo file .mp3 sono supportati.", ephemeral=True)
            return

        assert interaction.guild_id is not None
        await interaction.response.defer(thinking=True, ephemeral=True)
        success = await save_intro_file(file, interaction.user.id, interaction.guild_id, temp=True)
        if success:
            temp_path = get_intro_path(interaction.user.id, interaction.guild_id, temp=True)
            if await validate_audio_file(temp_path, INTRO_MAX_SECONDS):
                os.replace(temp_path, get_intro_path(interaction.user.id, interaction.guild_id))
                await interaction.followup.send("✅ Intro salvato con successo!")
            else:
                os.remove(temp_path)
                await interaction.followup.send("❌ Il file audio non è valido o supera la durata massima.")
        else:
            await interaction.followup.send("❌ Errore durante il salvataggio del file.")

    @app_commands.command(name="intro-youtube", description="Carica un file intro da un video YouTube")
    @app_commands.describe(time_start="Orario di inizio in formato HH:MM:SS", time_end="Orario di fine in formato HH:MM:SS", url="Link del video YouTube")
    @is_guild_context()
    async def intro_youtube(self, interaction: discord.Interaction, time_start: str, time_end: str, url: str) -> None:
        assert interaction.guild_id is not None
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not validate_time_format(time_start) or not validate_time_format(time_end):
            await interaction.followup.send("❌ Formato di time_start o time_end non valido. Usa HH:MM:SS o MM:SS.", ephemeral=True)
            return

        success = await download_audio_clip(interaction.user.id, interaction.guild_id, url, time_start, time_end)

        if success:
            await interaction.followup.send(f"✅ Intro caricato con successo da YouTube (max {INTRO_MAX_SECONDS}s)!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Errore durante il download o il salvataggio dell'audio.", ephemeral=True)

    @app_commands.command(name="intro-delete", description="Cancella il tuo file intro")
    @is_guild_context()
    async def delete_intro(self, interaction: discord.Interaction) -> None:
        assert interaction.guild_id is not None
        deleted = delete_intro_file(interaction.user.id, interaction.guild_id)
        if deleted:
            await interaction.response.send_message("🗑️ Intro cancellato con successo!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Nessun file intro trovato.", ephemeral=True)

    @app_commands.command(name="intro-info", description="Mostra informazioni sul tuo file intro attuale")
    @is_guild_context()
    async def intro_info(self, interaction: discord.Interaction) -> None:
        assert interaction.guild_id is not None
        path = get_intro_path(interaction.user.id, interaction.guild_id)

        if not os.path.exists(path):
            await interaction.response.send_message("ℹ️ Non hai ancora caricato un file intro.", ephemeral=True)
            return

        file_size = os.path.getsize(path)
        creation_time = os.path.getctime(path)
        timestamp = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")

        await interaction.response.send_message(f"🎵 Intro trovato!\n- **Dimensione**: {round(file_size / 1024, 2)} KB\n- **Creato il**: {timestamp}", ephemeral=True)

    @app_commands.command(name="intro-play", description="Riproduci il tuo file intro nel canale vocale attuale")
    @is_guild_context()
    async def intro_play(self, interaction: discord.Interaction) -> None:
        assert interaction.guild_id is not None
        voice_state = interaction.user.voice  # type: ignore[union-attr]

        if not voice_state or not voice_state.channel:
            await interaction.response.send_message("❌ Devi essere in un canale vocale per usare questo comando.", ephemeral=True)
            return

        path = get_intro_path(interaction.user.id, interaction.guild_id)
        if not os.path.exists(path):
            await interaction.response.send_message("⚠️ Nessun file intro trovato per te in questo server.", ephemeral=True)
            return

        vc: discord.VoiceClient | None = None
        try:
            # guild.voice_client è tipizzato come VoiceProtocol | None negli stubs; a runtime è VoiceClient
            voice_client = cast(discord.VoiceClient | None, interaction.guild.voice_client)  # type: ignore[union-attr]
            if voice_client and voice_client.is_connected():
                if voice_client.is_playing():
                    await interaction.response.send_message("❌ Il bot sta già riproducendo un audio.", ephemeral=True)
                    return
                if voice_client.channel != voice_state.channel:
                    await voice_client.move_to(voice_state.channel)
                vc = voice_client
            else:
                # connect() è tipizzato come VoiceProtocol negli stubs; a runtime è VoiceClient
                vc = cast(discord.VoiceClient, await voice_state.channel.connect())

            vc.play(discord.FFmpegPCMAudio(path, executable=FFMPEG_PATH, before_options=f"-t {INTRO_MAX_SECONDS} -loglevel panic"))
            await interaction.response.send_message("🎶 Intro in riproduzione...", ephemeral=True)

            timeout: float = 0
            max_timeout = INTRO_MAX_SECONDS + 2
            while vc.is_playing() and timeout < max_timeout:
                await asyncio.sleep(0.5)
                timeout += 0.5

        except discord.ClientException as e:
            await interaction.response.send_message(f"❌ Errore di connessione vocale: {e}", ephemeral=True)
        except OSError as e:
            await interaction.response.send_message(f"❌ Errore di accesso al file audio: {e}", ephemeral=True)
        finally:
            if vc and vc.is_connected():
                await vc.disconnect()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(IntroManager(bot))
