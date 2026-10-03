import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

from config import COMMAND_PREFIXES
from utils.formatters import clean_html, format_duration
from utils.soundcloud import soundcloud
from utils.queue import queue_mgr
from utils.thumbnail import thumbnail_gen
from core.call import call_manager
from utils.inline import player_keyboard

TRENDING_CACHE = {}

def _fetch_trending():
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
            # Query trending soundcloud electronic / popular tracks
            res = ydl.extract_info("scsearch6:trending music", download=False)
            if not res or "entries" not in res:
                return []
            tracks = []
            for entry in res["entries"][:6]:
                tracks.append({
                    "id": entry.get("id"),
                    "title": entry.get("title", "Unknown"),
                    "uploader": entry.get("uploader") or "SoundCloud Artist",
                    "duration_sec": int(entry.get("duration") or 0),
                    "url": entry.get("url") or entry.get("webpage_url"),
                })
            return tracks
        except Exception:
            return []

@Client.on_message(filters.command(["trending", "top", "charts"], prefixes=COMMAND_PREFIXES) & filters.group)
async def trending_cmd(client: Client, message: Message):
    status = await message.reply_text("🔥 <i>Fetching SoundCloud Trending Charts...</i>")

    tracks = await asyncio.to_thread(_fetch_trending)
    if not tracks:
        return await status.edit_text("❌ Could not fetch trending charts.")

    TRENDING_CACHE[message.chat.id] = tracks

    text = "🔥 <b>SoundCloud Trending Charts Right Now:</b>\n\n"
    buttons = []
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]

    row1 = []
    row2 = []
    for idx, t in enumerate(tracks):
        dur = format_duration(t["duration_sec"])
        text += f"{emojis[idx]} <b>{clean_html(t['title'])}</b>\n"
        text += f"    👤 <i>{clean_html(t['uploader'])}</i> | ⏱ <code>{dur}</code>\n\n"

        btn = InlineKeyboardButton(f"▶️ {emojis[idx]}", callback_data=f"trend_{message.chat.id}_{idx}")
        if idx < 3:
            row1.append(btn)
        else:
            row2.append(btn)

    buttons.append(row1)
    if row2:
        buttons.append(row2)
    buttons.append([InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{message.chat.id}")])

    await status.delete()
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Client.on_callback_query(filters.regex(r"^trend_(-?\d+)_(\d+)$"))
async def cb_play_trending(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    idx = int(query.matches[0].group(2))

    tracks = TRENDING_CACHE.get(chat_id)
    if not tracks or idx >= len(tracks):
        return await query.answer("Trending list expired.", show_alert=True)

    selected = tracks[idx]
    await query.answer(f"Loading: {selected['title'][:20]}...")

    status = await client.send_message(chat_id, f"⚡ <i>Fetching stream for:</i> <b>{clean_html(selected['title'])}</b>...")
    track = await soundcloud.get_track(selected["url"])

    if not track or not track.get("stream_url"):
        return await status.edit_text("❌ Failed to resolve audio stream.")

    requester = query.from_user.mention
    track["requester_mention"] = requester
    track["requester_id"] = query.from_user.id

    is_playing = bool(queue_mgr.get_current(chat_id))

    if is_playing:
        pos = queue_mgr.add(chat_id, track)
        await status.delete()
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
            track_id=str(track.get("id", "trend")),
        )

        caption = (
            f"☁️ <b>Now Streaming on SoundCloud:</b>\n\n"
            f"🎵 <b>Title:</b> <a href=\"{track['url']}\">{clean_html(track['title'])}</a>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
            f"⏱ <b>Duration:</b> <code>{format_duration(track.get('duration_sec', 0))}</code>\n"
            f"🎧 <b>Requested by:</b> {requester}\n\n"
            f"<blockquote>⚡ <i>Trending Hit on SoundCloud</i></blockquote>"
        )

        keyboard = player_keyboard(
            chat_id=chat_id,
            is_paused=False,
            loop_mode=queue_mgr.get_loop(chat_id),
            sc_url=track.get("url", ""),
        )

        await status.delete()
        await client.send_photo(chat_id, photo=thumb_path, caption=caption, reply_markup=keyboard)

    except Exception as e:
        await status.edit_text(f"❌ <b>Streaming Error:</b> <code>{clean_html(str(e))}</code>")
