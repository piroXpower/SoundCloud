from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.filters import is_admin_or_auth, reload_admin_cache


@bot.on_message(filters.command(["reload", "admincache"]) & filters.group)
async def reload_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    reload_admin_cache(chat_id)
    await message.reply_text("🔄 <b>Admin list and permissions cache have been refreshed!</b>")
