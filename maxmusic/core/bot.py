import logging
import pyrogram
from pyrogram.enums import ParseMode
from pyrogram.types import LinkPreviewOptions
from maxmusic.config import config

logger = logging.getLogger(__name__)


class Bot(pyrogram.Client):
    def __init__(self):
        super().__init__(
            name="MaxMusicBot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=ParseMode.HTML,
            workers=8,
            max_concurrent_transmissions=4,
            in_memory=True,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )

    async def boot(self):
        await self.start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        logger.info(f"Bot started successfully as @{self.username}")
        try:
            await self.send_message(
                config.LOGGER_ID,
                f"<b>🚀 {config.BOT_NAME} Started</b>\n\n"
                f"<b>ID:</b> <code>{self.id}</code>\n"
                f"<b>Username:</b> @{self.username}"
            )
        except Exception as e:
            logger.warning(f"Failed to post to LOGGER_ID ({config.LOGGER_ID}): {e}")

    async def exit(self):
        try:
            await self.stop()
        except Exception:
            pass
        logger.info("Bot client stopped.")


bot = Bot()
