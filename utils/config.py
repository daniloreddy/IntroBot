# utils/config.py

import logging
import os
import time

from dotenv import load_dotenv

load_dotenv()

BOT_START_TIME = time.time()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- General Settings ---
DEFAULT_LANG = "en"
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "../data"))
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
INTRO_DIR = os.path.normpath(os.path.join(DATA_DIR, "intros"))
if not os.path.exists(INTRO_DIR):
    os.makedirs(INTRO_DIR)


# --- Admin Settings ---
DISCORD_ADMIN_ROLES = ["Admin", "Boss", "CoffyMaster"]
DISCORD_FALLBACK_ID = int(os.getenv("DISCORD_FALLBACK_ID", "123456789012345678"))  # Default fallback ID

# --- Logging ---
LOG_DIR = os.path.normpath(os.path.join(BASE_DIR, "../logs"))
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
BOT_LOG_FILE = "bot.log"
SERVICE_LOG_FILE = "services.log"
ERROR_LOG_FILE = "errors.log"

# --- API Keys ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "__unset__")
if DISCORD_BOT_TOKEN == "__unset__":
    raise ValueError("Variabile d'ambiente DISCORD_BOT_TOKEN non impostata!")

# --- FFmpeg ---
# Percorso al binario ffmpeg. Impostare FFMPEG_PATH in .env se non è nel PATH di sistema.
# Esempio: FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
# ffprobe è derivato automaticamente dalla stessa directory di ffmpeg, ma può essere sovrascritto.
_ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
FFPROBE_PATH: str = os.getenv(
    "FFPROBE_PATH",
    os.path.join(_ffmpeg_dir, "ffprobe") if _ffmpeg_dir else "ffprobe",
)

# --- Intro Settings ---
INTRO_MAX_SECONDS = 11  # Limite massimo di riproduzione per ogni intro

# --- Logging ---
LOG_LEVEL_ENV = os.getenv("LOG_LEVEL", "INFO")
valid_levels = logging.getLevelNamesMapping()
if LOG_LEVEL_ENV not in valid_levels:
    raise ValueError(f"Livello di log '{LOG_LEVEL_ENV}' non valido. Valori validi: {list(valid_levels.keys())}")
LOG_LEVEL = valid_levels[LOG_LEVEL_ENV]  # Define the log level for use in logger.py
