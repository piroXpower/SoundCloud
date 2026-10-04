from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.calls import calls
from maxmusic.core.database import db
from maxmusic.helpers.buttons import speed_markup
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["speed", "playbackspeed", "cspeed"]) & filters.group)
async def speed_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No active stream.")

    await message.reply_text(
        "⚡ <b>Playback Speed</b>\n\nChoose speed multiplier for the voice chat stream:",
        reply_markup=speed_markup(chat_id)
    )
