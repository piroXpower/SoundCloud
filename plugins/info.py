from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import COMMAND_PREFIXES
from utils.queue import queue_mgr
from utils.formatters import clean_html, format_duration

@Client.on_message(filters.command(["trackinfo", "now", "current"], prefixes=COMMAND_PREFIXES))
async def track_info_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)

    if not curr:
        return await message.reply_text("❌ Nothing is currently streaming in this chat.")

    dur = format_duration(curr.get("duration_sec", 0))
    vol = queue_mgr.get_volume(chat_id)
    loop = queue_mgr.get_loop(chat_id)
    is_paused = queue_mgr.is_paused(chat_id)

    text = (
        f"🎧 <b>Currently Streaming SoundCloud Track:</b>\n\n"
        f"🎵 <b>Title:</b> <code>{clean_html(curr['title'])}</code>\n"
        f"👤 <b>Artist:</b> <code>{clean_html(curr['uploader'])}</code>\n"
        f"⏱ <b>Duration:</b> <code>{dur}</code>\n"
        f"🎧 <b>Requested by:</b> {curr.get('requester_mention', 'Listener')}\n\n"
        f"📊 <b>Audio Stream Details:</b>\n"
        f" • <b>Volume:</b> <code>{vol}%</code>\n"
        f" • <b>Status:</b> <code>{'Paused ⏸' if is_paused else 'Playing ▶️'}</code>\n"
        f" • <b>Loop:</b> <code>{loop.capitalize()}</code>\n"
        f" • <b>Bitrate:</b> <code>320 kbps (High Fidelity)</code>\n"
        f" • <b>Platform:</b> <code>SoundCloud Web Stream</code>\n"
    )

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("☁️ Listen on SoundCloud", url=curr.get("url", "https://soundcloud.com")),
            InlineKeyboardButton("📜 Queue", callback_data=f"ctrl_queue_{chat_id}_0"),
        ]
    ])

    await message.reply_text(text, reply_markup=btn, disable_web_page_preview=True)

@Client.on_message(filters.command(["id", "chatid"], prefixes=COMMAND_PREFIXES))
async def id_cmd(client: Client, message: Message):
    chat = message.chat
    user = message.from_user

    text = (
        f"🆔 <b>Chat & User Identification:</b>\n\n"
        f"💬 <b>Chat Title:</b> <code>{clean_html(chat.title or 'Private')}</code>\n"
        f"🏷 <b>Chat ID:</b> <code>{chat.id}</code>\n"
        f"👥 <b>Chat Type:</b> <code>{chat.type.name}</code>\n\n"
    )
    if user:
        text += (
            f"👤 <b>User:</b> {user.mention}\n"
            f"🏷 <b>User ID:</b> <code>{user.id}</code>\n"
            f"📛 <b>Username:</b> @{user.username or 'None'}\n"
        )

    await message.reply_text(text)
