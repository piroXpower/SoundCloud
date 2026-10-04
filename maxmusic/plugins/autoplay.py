from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.queue import queue_mgr
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["autoplay"]) & filters.group)
async def autoplay_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if len(message.command) < 2:
        state = "Enabled" if queue_mgr.is_autoplay(chat_id) else "Disabled"
        return await message.reply_text(
            f"✨ <b>Autoplay Status:</b> {state}\n\n"
            f"When enabled, the bot automatically continues playing recommended tracks after the queue finishes.\n\n"
            f"• <code>/autoplay on</code>\n"
            f"• <code>/autoplay off</code>"
        )

    arg = message.command[1].lower()
    if arg in ("on", "enable", "true", "yes"):
        queue_mgr.set_autoplay(chat_id, True)
        await message.reply_text("✨ <b>Autoplay has been enabled for this group.</b>")
    elif arg in ("off", "disable", "false", "no"):
        queue_mgr.set_autoplay(chat_id, False)
        await message.reply_text("🚫 <b>Autoplay has been disabled for this group.</b>")
    else:
        await message.reply_text("Usage: <code>/autoplay [on|off]</code>")
