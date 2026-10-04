from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.calls import calls
from maxmusic.core.database import db
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["mute", "vcmute"]) & filters.group)
async def mute_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No active stream.")

    success = await calls.mute(chat_id)
    if success:
        await message.reply_text("🔇 <b>Assistant muted in Voice Chat.</b>")
    else:
        await message.reply_text("❌ Failed to mute assistant.")


@bot.on_message(filters.command(["unmute", "vcunmute"]) & filters.group)
async def unmute_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No active stream.")

    success = await calls.unmute(chat_id)
    if success:
        await message.reply_text("🔊 <b>Assistant unmuted in Voice Chat.</b>")
    else:
        await message.reply_text("❌ Failed to unmute assistant.")
