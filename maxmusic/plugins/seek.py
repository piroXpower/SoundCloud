from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.calls import calls
from maxmusic.core.database import db
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["seek", "cseek"]) & filters.group)
async def seek_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No active stream.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: <code>/seek [seconds]</code> (e.g. <code>/seek 30</code>)")

    try:
        seconds = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Please specify valid seconds integer.")

    success = await calls.seek(chat_id, seconds)
    if success:
        await message.reply_text(f"⏩ <b>Seeked to {seconds} seconds.</b>")
    else:
        await message.reply_text("❌ Failed to seek.")


@bot.on_message(filters.command(["seekback", "rseek"]) & filters.group)
async def seekback_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No active stream.")

    seconds = 10
    if len(message.command) > 1:
        try:
            seconds = int(message.command[1])
        except ValueError:
            pass

    success = await calls.seek(chat_id, max(0, seconds))
    if success:
        await message.reply_text(f"⏪ <b>Seeked back by {seconds} seconds.</b>")
