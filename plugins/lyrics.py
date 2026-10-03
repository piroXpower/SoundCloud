import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.queue import queue_mgr
from utils.formatters import clean_html

async def fetch_lyrics(title: str, artist: str = "") -> str:
    url = f"https://api.lyrics.ovh/v1/{artist}/{title}" if artist else f"https://api.lyrics.ovh/v1/a/{title}"
    try:
        async with aiohttp.ClientSession() as session:
            # First try direct artist/title
            if artist:
                async with session.get(f"https://api.lyrics.ovh/v1/{artist}/{title}", timeout=8) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("lyrics"):
                            return data["lyrics"]

            # Fallback search query
            clean_title = title.split("-")[0].split("(")[0].strip()
            async with session.get(f"https://api.lyrics.ovh/v1/{artist or 'song'}/{clean_title}", timeout=8) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("lyrics", "")
    except Exception:
        pass
    return ""

@Client.on_message(filters.command(["lyrics", "lyric"], prefixes=COMMAND_PREFIXES))
async def lyrics_cmd(client: Client, message: Message):
    title = ""
    artist = ""

    if len(message.command) > 1:
        query = " ".join(message.command[1:])
        if "-" in query:
            parts = query.split("-", 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            title = query.strip()
    else:
        # Check currently playing track in chat
        curr = queue_mgr.get_current(message.chat.id)
        if curr:
            title = curr.get("title", "")
            artist = curr.get("uploader", "")
        else:
            return await message.reply_text(
                "📜 <b>Usage:</b> <code>/lyrics [song name]</code>\n"
                "Example: <code>/lyrics Coldplay - Yellow</code>"
            )

    status = await message.reply_text(f"🔍 <i>Searching lyrics for:</i> <b>{clean_html(title)}</b>...")
    lyrics = await fetch_lyrics(title, artist)

    if not lyrics:
        return await status.edit_text(f"❌ <b>Lyrics Not Found!</b> Could not find lyrics for <code>{clean_html(title)}</code>.")

    # Truncate if Telegram 4096 character limit
    display_lyrics = lyrics[:3800] + "..." if len(lyrics) > 3800 else lyrics

    text = (
        f"🎤 <b>Lyrics for:</b> <code>{clean_html(title)}</code>\n\n"
        f"<blockquote>{display_lyrics}</blockquote>"
    )

    btn = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Close", callback_data="close_lyrics")]])
    await status.delete()
    await message.reply_text(text, reply_markup=btn)

@Client.on_callback_query(filters.regex("^close_lyrics$"))
async def cb_close_lyrics(client: Client, query: CallbackQuery):
    await query.message.delete()
