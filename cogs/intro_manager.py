import os
from datetime import datetime
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from utils.file_utils import save_intro_file, delete_intro_file, get_intro_path, download_audio_clip, validate_audio_file, validate_time_format
from utils.checks import is_guild_context
from utils.config import INTRO_MAX_SECONDS


class IntroManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="intro_set_volume", description="Imposta il volume di riproduzione della tua intro (0.0 a 1.0)")
    @app_commands.describe(volume="Il livello del volume (es. 0.5 per metà volume)")
    @is_guild_context()
    async def set_volume(self, interaction: discord.Interaction, volume: float):
        """Set the playback volume for the user's intro."""
        if not 0.0 <= volume <= 1.0:
            await interaction.response.send_message("❌ Il volume deve essere tra 0.0 e 1.0.", ephemeral=True)
            return
        # TODO: Salva il volume in una struttura persistente (es. database o dizionario)
        await interaction.response.send_message(f"✅ Volume impostato a {volume}.", ephemeral=True)

    @app_commands.command(name="intro-upload", description="Carica o sovrascrivi il tuo file intro")
    @is_guild_context()
    async def upload_intro(self, interaction: discord.Interaction, file: discord.Attachment):
        if not file.filename.lower().endswith((".mp3", ".wav")):
            await interaction.response.send_message("❌ Solo file .mp3 o .wav sono supportati.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        success = await save_intro_file(file, interaction.user.id, interaction.guild.id)
        if success:
            path = get_intro_path(interaction.user.id, interaction.guild.id)
            if validate_audio_file(path, INTRO_MAX_SECONDS):
                await interaction.followup.send("✅ Intro salvato con successo!")
            else:
                delete_intro_file(interaction.user.id, interaction.guild.id)
                await interaction.followup.send("❌ Il file audio non è valido o supera la durata massima.")
        else:
            await interaction.followup.send("❌ Errore durante il salvataggio del file.")

    @app_commands.command(name="intro-youtube", description="Carica un file intro da un video YouTube")
    @app_commands.describe(
        time_start="Orario di inizio in formato HH:MM:SS",
        time_end="Orario di fine in formato HH:MM:SS",
        url="Link del video YouTube"
    )
    @is_guild_context()
    async def intro_youtube(self, interaction: discord.Interaction, time_start: str, time_end: str, url: str):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not validate_time_format(time_start) or not validate_time_format(time_end):
            await interaction.response.send_message("❌ Formato di time_start o time_end non valido. Usa HH:MM:SS o MM:SS.", ephemeral=True)
            return

        success = await download_audio_clip(interaction.user.id, interaction.guild.id, url, time_start, time_end)

        if success:
            await interaction.followup.send(f"✅ Intro caricato con successo da YouTube (max {INTRO_MAX_SECONDS}s)!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Errore durante il download o il salvataggio dell'audio.", ephemeral=True)

    @app_commands.command(name="intro-delete", description="Cancella il tuo file intro")
    @is_guild_context()
    async def delete_intro(self, interaction: discord.Interaction):
        deleted = delete_intro_file(interaction.user.id, interaction.guild.id)
        if deleted:
            await interaction.response.send_message("🗑️ Intro cancellato con successo!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Nessun file intro trovato.", ephemeral=True)
    
    @app_commands.command(name="intro-info", description="Mostra informazioni sul tuo file intro attuale")
    @is_guild_context()
    async def intro_info(self, interaction: discord.Interaction):
        path = get_intro_path(interaction.user.id, interaction.guild.id)

        if not os.path.exists(path):
            await interaction.response.send_message("ℹ️ Non hai ancora caricato un file intro.", ephemeral=True)
            return

        file_size = os.path.getsize(path)
        creation_time = os.path.getctime(path)
        
        timestamp = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")

        await interaction.response.send_message(
            f"🎵 Intro trovato!\n"
            f"- **Dimensione**: {round(file_size / 1024, 2)} KB\n"
            f"- **Creato il**: {timestamp}",
            ephemeral=True
            )
    
    @app_commands.command(name="intro-play", description="Riproduci il tuo file intro nel canale vocale attuale")
    @is_guild_context()
    async def intro_play(self, interaction: discord.Interaction):
        voice_state = interaction.user.voice

        if not voice_state or not voice_state.channel:
            await interaction.response.send_message("❌ Devi essere in un canale vocale per usare questo comando.", ephemeral=True)
            return

        path = get_intro_path(interaction.user.id, interaction.guild.id)
        if not os.path.exists(path):
            await interaction.response.send_message("⚠️ Nessun file intro trovato per te in questo server.", ephemeral=True)
            return

        try:
            voice_client = interaction.guild.voice_client
            if voice_client and voice_client.is_connected():
                if voice_client.channel != voice_state.channel:
                    await voice_client.move_to(voice_state.channel)
                if voice_client.is_playing():
                    await interaction.response.send_message("❌ Il bot sta già riproducendo un audio.", ephemeral=True)
                    return
                vc = voice_client
            else:
                vc = await voice_state.channel.connect()

            vc.play(discord.FFmpegPCMAudio(path, before_options=f"-t {INTRO_MAX_SECONDS} -loglevel panic"))
            await interaction.response.send_message("🎶 Intro in riproduzione...", ephemeral=True)

            while vc.is_playing():
                await asyncio.sleep(0.5)
            await vc.disconnect()

        except discord.ClientException as e:
            await interaction.response.send_message(f"❌ Errore di connessione vocale: {e}", ephemeral=True)
        except OSError as e:
            await interaction.response.send_message(f"❌ Errore di accesso al file audio: {e}", ephemeral=True)



async def setup(bot):
    await bot.add_cog(IntroManager(bot))
