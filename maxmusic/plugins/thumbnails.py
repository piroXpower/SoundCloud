from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["thumb", "setthumb"]) & filters.group)
async def set_thumb_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    reply = message.reply_to_message
    if not reply or not reply.photo:
        return await message.reply_text("Usage: Reply to a photo with <code>/setthumb</code> to set custom thumbnail.")

    path = await bot.download_media(reply.photo, file_name=f"cache/custom_thumb_{chat_id}.jpg")
    await db.update_chat_setting(chat_id, "custom_thumb", path)
    await message.reply_text("✅ Custom thumbnail updated for this chat!")


@bot.on_message(filters.command(["delthumb", "clearthumb"]) & filters.group)
async def del_thumb_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    await db.update_chat_setting(chat_id, "custom_thumb", None)
    await message.reply_text("🗑 Custom thumbnail removed. Restored default artwork.")
