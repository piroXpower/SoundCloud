from pyrogram import filters, types
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.config import config


@bot.on_message(filters.command(["start"]))
async def start_command(_, message: types.Message):
    user = message.from_user
    chat = message.chat

    # Track chat & user in database
    if user:
        await db._db.users.update_one({"user_id": user.id}, {"$set": {"user_id": user.id, "name": user.first_name}}, upsert=True)
    if chat.type in (types.ChatType.GROUP, types.ChatType.SUPERGROUP):
        await db._db.chats.update_one({"chat_id": chat.id}, {"$set": {"chat_id": chat.id, "title": chat.title}}, upsert=True)
        return await message.reply_text(
            f"👋 Hey! I am <b>{config.BOT_NAME}</b>.\n"
            f"Ready to stream high quality music & video in this group!\n"
            f"Type <code>/help</code> for available commands."
        )

    # Private Chat Start Menu
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Me To Your Group", url=f"https://t.me/{bot.username}?startgroup=true"),
        ],
        [
            InlineKeyboardButton("📖 Help & Commands", callback_data="help_main"),
            InlineKeyboardButton("⚙️ Settings", callback_data=f"cb_settings_{chat.id}"),
        ],
        [
            InlineKeyboardButton("💬 Support Chat", url=config.SUPPORT_CHAT),
            InlineKeyboardButton("📢 Updates Channel", url=config.SUPPORT_CHANNEL),
        ],
    ])

    text = (
        f"👋 <b>Welcome, {user.mention if user else 'Music Lover'}!</b>\n\n"
        f"I am <b>{config.BOT_NAME}</b>, a next-generation Telegram Voice Chat music and video streaming bot.\n\n"
        f"✨ <b>Features:</b>\n"
        f"• Crystal clear 320kbps audio & 720p HD video\n"
        f"• Full YouTube, Playlist & Telegram file support\n"
        f"• Channel Play (stream in connected channels)\n"
        f"• Continuous smart Autoplay & custom loop modes\n\n"
        f"Tap the buttons below to explore commands or add me to your group!"
    )

    if config.START_IMG:
        try:
            return await message.reply_photo(config.START_IMG, caption=text, reply_markup=keyboard)
        except Exception:
            pass

    await message.reply_text(text, reply_markup=keyboard)
