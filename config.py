import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API Credentials
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# PyTgCalls Assistant String Session (Telegram User Account)
# Generate with: python3 -m pyrogram
SESSION_STRING = os.getenv("SESSION_STRING", "")

# Bot Owner & Sudo Users (Comma-separated Telegram user IDs)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUDO_USERS = [int(x) for x in os.getenv("SUDO_USERS", "").split() if x.isdigit()]
if OWNER_ID and OWNER_ID not in SUDO_USERS:
    SUDO_USERS.append(OWNER_ID)

# Bot Configuration
BOT_NAME = os.getenv("BOT_NAME", "SoundCloud Music")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
COMMAND_PREFIXES = ["/", "!", ".", "?"]

# Audio Quality & Streaming Settings
DEFAULT_VOLUME = int(os.getenv("DEFAULT_VOLUME", "100"))
DURATION_LIMIT_MINUTES = int(os.getenv("DURATION_LIMIT_MINUTES", "180")) # 3 hours max per track

# Support & Updates Links
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "https://t.me/")
UPDATES_CHANNEL = os.getenv("UPDATES_CHANNEL", "https://t.me/")
START_IMAGE_URL = os.getenv(
    "START_IMAGE_URL",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?q=80&w=1280&auto=format&fit=crop"
)
