import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


def _to_bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "t", "y", "on")


def _to_int(val: str | None, default: int = 0) -> int:
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


class Config:
    def __init__(self):
        # Telegram API
        self.API_ID: int = _to_int(os.getenv("API_ID"))
        self.API_HASH: str = os.getenv("API_HASH", "").strip()
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

        # Bot Ownership & Logging
        self.OWNER_ID: int = _to_int(os.getenv("OWNER_ID"))
        self.LOGGER_ID: int = _to_int(os.getenv("LOGGER_ID"))

        # Database
        self.MONGO_URL: str = os.getenv("MONGO_URL", "").strip()
        self.DB_NAME: str = os.getenv("DB_NAME", "MaxMusicV2").strip()

        # Assistant Sessions (Multi-Assistant)
        self.SESSION1: str | None = os.getenv("SESSION1") or os.getenv("SESSION")
        self.SESSION2: str | None = os.getenv("SESSION2")
        self.SESSION3: str | None = os.getenv("SESSION3")

        # Playback Limits
        self.DURATION_LIMIT: int = _to_int(os.getenv("DURATION_LIMIT", "14400"), 14400)
        self.QUEUE_LIMIT: int = _to_int(os.getenv("QUEUE_LIMIT", "30"), 30)
        self.PLAYLIST_LIMIT: int = _to_int(os.getenv("PLAYLIST_LIMIT", "30"), 30)

        # Automation
        self.AUTO_LEAVE: bool = _to_bool(os.getenv("AUTO_LEAVE", "True"), True)
        self.AUTO_END: bool = _to_bool(os.getenv("AUTO_END", "True"), True)
        self.AUTO_LEAVE_TIME: int = _to_int(os.getenv("AUTO_LEAVE_TIME", "300"), 300)
        self.CLEAN_MODE: bool = _to_bool(os.getenv("CLEAN_MODE", "True"), True)

        # Branding & URLs
        self.BOT_NAME: str = os.getenv("BOT_NAME", "Max Music")
        self.SUPPORT_CHANNEL: str = os.getenv("SUPPORT_CHANNEL", "https://t.me/ArchonNetwork")
        self.SUPPORT_CHAT: str = os.getenv("SUPPORT_CHAT", "https://t.me/BeMySugarBaby")
        self.START_IMG: str = os.getenv(
            "START_IMG",
            "https://graph.org/file/e8e15d589c6883f5e67da-abd39e5eab54f88ddb.mp4"
        )
        self.PING_IMG: str = os.getenv(
            "PING_IMG",
            "https://graph.org/file/0f6a1047af20de24183af-ca71bf5f61dda70013.jpg"
        )
        self.DEFAULT_THUMB: str = os.getenv(
            "DEFAULT_THUMB",
            "https://graph.org/file/916d4d3ed43fcfa4766bb-420186b24e6dc552e0.jpg"
        )

        # YouTube & Cookies
        self.YOUTUBE_COOKIES_FILE: str = os.getenv("YOUTUBE_COOKIES_FILE", "cookies.txt")
        cookies_raw = os.getenv("COOKIES_URL", "")
        self.COOKIES_URL: List[str] = [u.strip() for u in cookies_raw.split() if u.strip()]

        # Localization
        self.LANG_CODE: str = os.getenv("LANG_CODE", "en")

    def check(self):
        missing = []
        for key in ["API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL", "OWNER_ID", "LOGGER_ID"]:
            if not getattr(self, key):
                missing.append(key)
        if not (self.SESSION1 or self.SESSION2 or self.SESSION3):
            missing.append("SESSION1 (or SESSION)")

        if missing:
            raise SystemExit(
                f"[CONFIG ERROR] Missing required environment variables:\n -> "
                + "\n -> ".join(missing)
            )


config = Config()
