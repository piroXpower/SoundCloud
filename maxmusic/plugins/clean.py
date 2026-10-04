from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["cleanmode"]) & filters.group)
async def cleanmode_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    if len(message.command) < 2:
        settings = await db.get_chat_settings(chat_id)
        current = "Enabled" if settings.get("clean_mode", True) else "Disabled"
        return await message.reply_text(
            f"🧹 <b>Clean Mode Status:</b> {current}\n\n"
            f"When enabled, the bot automatically removes command messages after 5 seconds to keep chat tidy.\n\n"
            f"• <code>/cleanmode on</code>\n"
            f"• <code>/cleanmode off</code>"
        )

    arg = message.command[1].lower()
    enable = arg in ("on", "enable", "true", "yes")
    await db.update_chat_setting(chat_id, "clean_mode", enable)
    state = "Enabled" if enable else "Disabled"
    await message.reply_text(f"🧹 <b>Clean mode has been {state}.</b>")
