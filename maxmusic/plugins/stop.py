from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.calls import calls
from maxmusic.core.database import db
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["stop", "end"]) & filters.group)
async def stop_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Only Admins or Authorized DJs can stop playback.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No stream is currently playing.")

    await calls.stop(chat_id)
    await message.reply_text("⏹ <b>Playback stopped and queue cleared.</b>")
