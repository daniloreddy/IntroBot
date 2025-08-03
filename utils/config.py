# utils/config.py

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
INTRO_DIR = os.path.normpath(os.path.join(DATA_DIR, "../data"))
if not os.path.exists(INTRO_DIR):
    os.makedirs(INTRO_DIR)



# --- Admin Settings ---
DISCORD_ADMIN_ROLES = ["Admin", "Boss", "CoffyMaster"]
DISCORD_FALLBACK_ID = int(
    os.getenv("DISCORD_FALLBACK_ID", "123456789012345678")
)  # Default fallback ID

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

# --- Intro Settings ---
INTRO_MAX_SECONDS = 10  # Limite massimo di riproduzione per ogni intro

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
