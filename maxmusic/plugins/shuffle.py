from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.queue import queue_mgr
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["shuffle"]) & filters.group)
async def shuffle_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No active stream.")

    success = queue_mgr.shuffle(chat_id)
    if success:
        await message.reply_text("🔀 <b>Queue shuffled successfully!</b>")
    else:
        await message.reply_text("⚠️ Not enough songs in the queue to shuffle.")
