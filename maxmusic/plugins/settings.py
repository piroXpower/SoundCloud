from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.buttons import settings_markup
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["settings", "setting"]) & filters.group)
async def settings_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Only Admins can modify chat settings.")

    settings = await db.get_chat_settings(chat_id)
    text = (
        f"⚙️ <b>Chat Settings: {message.chat.title}</b>\n\n"
        f"• <b>Play Mode:</b> {settings.get('play_mode', 'Everyone')}\n"
        f"• <b>Clean Mode:</b> {'Enabled' if settings.get('clean_mode', True) else 'Disabled'}\n"
        f"• <b>Audio Quality:</b> {settings.get('quality', 'High').capitalize()}\n\n"
        f"Tap the buttons below to toggle configuration:"
    )

    await message.reply_text(text, reply_markup=settings_markup(chat_id, settings))
