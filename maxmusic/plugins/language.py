from pyrogram import filters, types
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import is_admin_or_auth

LANGUAGES = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 Hindi",
    "ar": "🇸🇦 Arabic",
    "es": "🇪🇸 Spanish",
    "fr": "🇫🇷 French",
    "ru": "🇷🇺 Russian",
}


@bot.on_message(filters.command(["lang", "language"]) & filters.group)
async def language_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    current_lang = await db.get_lang(chat_id)

    buttons = []
    row = []
    for code, name in LANGUAGES.items():
        row.append(InlineKeyboardButton(name, callback_data=f"cb_setlang_{chat_id}_{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🗑 Close", callback_data="cb_close")])

    await message.reply_text(
        f"🌐 <b>Language Settings</b>\n\n"
        f"<b>Current Language:</b> {LANGUAGES.get(current_lang, current_lang)}\n\n"
        f"Select your preferred language below:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
