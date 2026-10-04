from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.calls import calls
from maxmusic.core.database import db
from maxmusic.helpers.buttons import volume_markup
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["volume", "vol"]) & filters.group)
async def volume_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No active stream.")

    if len(message.command) < 2:
        return await message.reply_text(
            "🔊 <b>Volume Control</b>\n\nChoose a preset below or type <code>/volume [1-200]</code>:",
            reply_markup=volume_markup(chat_id)
        )

    try:
        vol = int(message.command[1])
        if not (1 <= vol <= 200):
            return await message.reply_text("❌ Volume must be between 1 and 200%.")
    except ValueError:
        return await message.reply_text("❌ Please enter a valid number.")

    await calls.set_volume(chat_id, vol)
    await message.reply_text(f"🔊 <b>Volume set to {vol}%</b>")
