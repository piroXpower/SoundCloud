from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.config import config


@bot.on_message(filters.video_chat_started & filters.group)
async def vc_started_handler(_, message: types.Message):
    try:
        await bot.send_message(
            config.LOGGER_ID,
            f"🔊 <b>Voice Chat Started</b>\n"
            f"Chat: {message.chat.title} (<code>{message.chat.id}</code>)"
        )
    except Exception:
        pass


@bot.on_message(filters.video_chat_ended & filters.group)
async def vc_ended_handler(_, message: types.Message):
    try:
        await bot.send_message(
            config.LOGGER_ID,
            f"🔇 <b>Voice Chat Ended</b>\n"
            f"Chat: {message.chat.title} (<code>{message.chat.id}</code>)"
        )
    except Exception:
        pass
