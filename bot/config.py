"""
Botning umumiy sozlamalari. Barcha maxfiy qiymatlar (.env) fayldan yoki
muhit o'zgaruvchilaridan (Railway -> Variables) olinadi.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Asosiy sozlamalar ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")

# --- Fayl yo'llari ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

GURUHLAR_FILE = DATA_DIR / "guruhlar.json"
USTOZLAR_FILE = DATA_DIR / "ustozlar.json"
XONALAR_FILE = DATA_DIR / "xonalar.json"
BOSHXONALAR_FILE = DATA_DIR / "boshxonalar.json"
HIERARCHY_CONFIG_FILE = DATA_DIR / "hierarchy_config.json"
DISPLAY_NAMES_FILE = DATA_DIR / "display_names.json"

SCREENSHOT_DIR = Path(os.getenv("SCREENSHOT_DIR", BASE_DIR / "tmp_screenshots"))
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# --- Web-admin porti (Railway avtomatik $PORT beradi) ---
ADMIN_PORT = int(os.getenv("PORT", os.getenv("ADMIN_PORT", 8000)))
