import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

from config import COMMAND_PREFIXES
from utils.soundcloud import soundcloud
from utils.formatters import clean_html, format_duration
from utils.queue import queue_mgr
from utils.thumbnail import thumbnail_gen
from core.call import call_manager
from utils.inline import player_keyboard

# In-memory search results cache: (chat_id, user_id) -> list of tracks
SEARCH_CACHE = {}

def _search_top_5(query: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "noplaylist": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            res = ydl.extract_info(f"scsearch5:{query}", download=False)
            if not res or "entries" not in res:
                return []
            tracks = []
            for entry in res["entries"][:5]:
                tracks.append({
                    "id": entry.get("id"),
                    "title": entry.get("title", "Unknown Title"),
                    "uploader": entry.get("uploader") or "SoundCloud Artist",
                    "duration_sec": int(entry.get("duration") or 0),
                    "url": entry.get("url") or entry.get("webpage_url"),
                })
            return tracks
        except Exception as e:
            print(f"[SoundCloud Search Error] {e}")
            return []

@Client.on_message(filters.command(["search", "scsearch"], prefixes=COMMAND_PREFIXES) & filters.group)
async def sc_search_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("🔍 <b>Usage:</b> <code>/search [query]</code>\nExample: <code>/search edm remix</code>")

    query = " ".join(message.command[1:])
    status = await message.reply_text(f"🔍 <i>Searching SoundCloud for</i> <code>{clean_html(query)}</code>...")

    results = await asyncio.to_thread(_search_top_5, query)
    if not results:
        return await status.edit_text("❌ No tracks found on SoundCloud for this query.")

    cache_key = f"{message.chat.id}_{message.from_user.id}"
    SEARCH_CACHE[cache_key] = results

    text = f"☁️ <b>SoundCloud Search Results for:</b> <code>{clean_html(query)}</code>\n\n"
    buttons = []
    num_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    row = []
    for idx, track in enumerate(results):
        dur = format_duration(track["duration_sec"])
        text += f"{num_emojis[idx]} <b>{clean_html(track['title'])}</b>\n"
        text += f"   👤 <i>{clean_html(track['uploader'])}</i> | ⏱ <code>{dur}</code>\n\n"
        row.append(InlineKeyboardButton(num_emojis[idx], callback_data=f"scsel_{idx}_{message.from_user.id}"))

    buttons.append(row)
    buttons.append([InlineKeyboardButton("🗑 Cancel", callback_data=f"scsel_cancel_{message.from_user.id}")])

    await status.delete()
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r"^scsel_(\d+)_(\d+)$"))
async def cb_select_search_track(client: Client, query: CallbackQuery):
    idx = int(query.matches[0].group(1))
    user_id = int(query.matches[0].group(2))
    chat_id = query.message.chat.id

    if query.from_user.id != user_id:
        return await query.answer("⚠️ This search menu belongs to someone else!", show_alert=True)

    cache_key = f"{chat_id}_{user_id}"
    results = SEARCH_CACHE.get(cache_key)

    if not results or idx >= len(results):
        return await query.answer("❌ Search expired. Please search again.", show_alert=True)

    selected = results[idx]
    await query.message.delete()
    
    # Process track
    status_msg = await client.send_message(chat_id, f"⚡ <i>Fetching stream for:</i> <b>{clean_html(selected['title'])}</b>...")
    track = await soundcloud.get_track(selected["url"])

    if not track or not track.get("stream_url"):
        return await status_msg.edit_text("❌ Failed to resolve audio stream.")

    requester = query.from_user.mention
    track["requester_mention"] = requester
    track["requester_id"] = query.from_user.id

    is_playing = bool(queue_mgr.get_current(chat_id))

    if is_playing:
        pos = queue_mgr.add(chat_id, track)
        await status_msg.delete()
        await client.send_message(
            chat_id,
            f"📋 <b>Added to Queue</b> [#{pos}]\n"
            f"🎵 <b>Title:</b> <code>{clean_html(track['title'])}</code>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
            f"🎧 <b>Requested by:</b> {requester}"
        )
        return

    try:
        await call_manager.play_or_change(chat_id, track["stream_url"])
        queue_mgr.set_current(chat_id, track)

        thumb_path = await thumbnail_gen.create_thumbnail(
            cover_url=track.get("thumbnail"),
            title=track.get("title", "Unknown"),
            artist=track.get("uploader", "SoundCloud Artist"),
            duration_sec=track.get("duration_sec", 0),
            track_id=str(track.get("id", "sc")),
        )

        caption = (
            f"☁️ <b>Now Streaming on SoundCloud:</b>\n\n"
            f"🎵 <b>Title:</b> <a href=\"{track['url']}\">{clean_html(track['title'])}</a>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
            f"⏱ <b>Duration:</b> <code>{format_duration(track.get('duration_sec', 0))}</code>\n"
            f"🎧 <b>Requested by:</b> {requester}\n\n"
            f"<blockquote>⚡ <i>Crystal-clear 320kbps audio directly from SoundCloud</i></blockquote>"
        )

        keyboard = player_keyboard(
            chat_id=chat_id,
            is_paused=False,
            loop_mode=queue_mgr.get_loop(chat_id),
            sc_url=track.get("url", ""),
        )

        await status_msg.delete()
        await client.send_photo(chat_id, photo=thumb_path, caption=caption, reply_markup=keyboard)

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Streaming Error:</b> <code>{clean_html(str(e))}</code>")

@Client.on_callback_query(filters.regex(r"^scsel_cancel_(\d+)$"))
async def cb_cancel_search(client: Client, query: CallbackQuery):
    user_id = int(query.matches[0].group(1))
    if query.from_user.id != user_id:
        return await query.answer("⚠️ You cannot close this menu!", show_alert=True)
    await query.message.delete()
