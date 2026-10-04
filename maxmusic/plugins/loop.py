from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.queue import queue_mgr
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["loop", "repeat"]) & filters.group)
async def loop_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if not db.is_call_active(chat_id):
        return await message.reply_text("⚠️ No active stream.")

    if len(message.command) < 2:
        current = queue_mgr.get_loop(chat_id)
        mode_str = "Disabled" if current == 0 else ("Single Track" if current == 1 else "Entire Queue")
        return await message.reply_text(
            f"🔁 <b>Current Loop Status:</b> {mode_str}\n\n"
            f"Usage:\n"
            f"• <code>/loop 0</code> or <code>/loop disable</code>: Turn loop off\n"
            f"• <code>/loop 1</code> or <code>/loop track</code>: Repeat current song\n"
            f"• <code>/loop 2</code> or <code>/loop queue</code>: Repeat full queue\n"
        )

    arg = message.command[1].lower()
    if arg in ("0", "disable", "off"):
        queue_mgr.set_loop(chat_id, 0)
        await message.reply_text("🔁 <b>Loop mode disabled.</b>")
    elif arg in ("1", "track", "song"):
        queue_mgr.set_loop(chat_id, 1)
        await message.reply_text("🔂 <b>Looping current track repeatedly.</b>")
    elif arg in ("2", "queue", "all"):
        queue_mgr.set_loop(chat_id, 2)
        await message.reply_text("🔁 <b>Looping entire queue.</b>")
    else:
        await message.reply_text("❌ Invalid mode. Choose 0, 1, or 2.")
