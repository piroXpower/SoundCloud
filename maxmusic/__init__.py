import logging
from logging.handlers import RotatingFileHandler
from maxmusic.config import config
from maxmusic.core.database import db
from maxmusic.core.bot import bot
from maxmusic.core.userbot import userbot
from maxmusic.core.calls import calls

__version__ = "2.0.0"

logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=3),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)

logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

logger = logging.getLogger("MaxMusic")
calls.set_bot(bot)
