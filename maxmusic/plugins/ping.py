import time
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.formatters import get_readable_time
from maxmusic.plugins.stats import BOT_START_TIME
from maxmusic.config import config


@bot.on_message(filters.command(["ping", "alive"]))
async def ping_command(_, message: types.Message):
    start = time.time()
    msg = await message.reply_text("🏓 <i>Pinging...</i>")
    delta_ms = int((time.time() - start) * 1000)
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))

    text = (
        f"⚡ <b>Pong!</b>\n\n"
        f"📶 <b>Response Latency:</b> <code>{delta_ms} ms</code>\n"
        f"⏱ <b>Uptime:</b> <code>{uptime}</code>\n"
        f"🤖 <b>Bot:</b> {config.BOT_NAME}\n"
    )

    if config.PING_IMG:
        try:
            await msg.delete()
            await message.reply_photo(config.PING_IMG, caption=text)
            return
        except Exception:
            pass

    await msg.edit_text(text)
