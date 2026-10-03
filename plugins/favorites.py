import os
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.queue import queue_mgr
from utils.formatters import clean_html, format_duration
from utils.soundcloud import soundcloud
from core.call import call_manager
from utils.thumbnail import thumbnail_gen
from utils.inline import player_keyboard

FAV_FILE = "/root/SoundCloudMusicBot/favorites.json"

def _load_favs() -> dict:
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_favs(data: dict):
    with open(FAV_FILE, "w") as f:
        json.dump(data, f, indent=2)

@Client.on_message(filters.command(["fav", "like"], prefixes=COMMAND_PREFIXES))
async def like_track_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    curr = queue_mgr.get_current(chat_id)

    if not curr:
        return await message.reply_text("❌ Nothing is currently playing to favorite.")

    data = _load_favs()
    user_favs = data.setdefault(user_id, [])

    # Check duplicate
    for t in user_favs:
        if t.get("url") == curr.get("url"):
            return await message.reply_text("❤️ <b>This track is already in your favorites!</b>")

    user_favs.append({
        "title": curr["title"],
        "uploader": curr["uploader"],
        "url": curr["url"],
        "duration_sec": curr.get("duration_sec", 0),
        "id": curr.get("id"),
    })
    _save_favs(data)

    await message.reply_text(
        f"❤️ <b>Added to your Favorites!</b>\n"
        f"🎵 <code>{clean_html(curr['title'])}</code>\n"
        f"Use <code>/favorites</code> to view your liked collection."
    )

@Client.on_message(filters.command(["favorites", "favs"], prefixes=COMMAND_PREFIXES))
async def view_favs_cmd(client: Client, message: Message):
    user_id = str(message.from_user.id)
    data = _load_favs()
    user_favs = data.get(user_id, [])

    if not user_favs:
        return await message.reply_text("💔 <b>No favorite tracks saved yet!</b> Use <code>/like</code> while listening.")

    text = f"❤️ <b>Your Liked SoundCloud Tracks ({len(user_favs)}):</b>\n\n"
    buttons = []
    
    for idx, t in enumerate(user_favs[:10], start=1):
        dur = format_duration(t.get("duration_sec", 0))
        text += f"<b>{idx}.</b> <a href=\"{t['url']}\">{clean_html(t['title'])}</a> (<code>{dur}</code>)\n"

    buttons.append([InlineKeyboardButton("🗑 Close", callback_data="fav_close")])

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Client.on_callback_query(filters.regex("^fav_close$"))
async def cb_close_fav(client: Client, query: CallbackQuery):
    await query.message.delete()
