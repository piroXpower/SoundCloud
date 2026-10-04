from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.calls import calls
from maxmusic.core.database import db
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["skip", "next"]) & filters.group)
async def skip_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Only Admins or Authorized DJs can skip tracks.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No stream is currently playing.")

    await message.reply_text("⏭ <b>Skipped to next track...</b>")
    await calls.play_next(chat_id)
