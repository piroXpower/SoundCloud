from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.soundcloud import soundcloud
from utils.queue import queue_mgr
from utils.thumbnail import thumbnail_gen
from core.call import call_manager
from utils.inline import player_keyboard
from utils.formatters import clean_html, format_duration

GENRE_MAP = {
    "phonk": ("🏎️ Phonk & Drift", "phonk drift 2024"),
    "deephouse": ("🏖️ Deep House", "deep house relaxing mix"),
    "hiphop": ("🎤 Hip-Hop & Rap", "hip hop rap beat"),
    "dubstep": ("💥 Dubstep & EDM", "dubstep bass drop mix"),
    "pop": ("✨ Pop & Acoustic", "acoustic pop top hits"),
    "lofi": ("☕ Chill Lofi Beats", "lofi chillhop study beats"),
    "synth": ("🌆 Synthwave & Cyber", "synthwave retrowave 80s"),
    "rock": ("🎸 Rock & Metal", "hard rock alternative hits"),
}

@Client.on_message(filters.command(["genres", "genre"], prefixes=COMMAND_PREFIXES) & filters.group)
async def genres_cmd(client: Client, message: Message):
    buttons = []
    items = list(GENRE_MAP.items())
    for i in range(0, len(items), 2):
        row = [
            InlineKeyboardButton(items[i][1][0], callback_data=f"genre_{message.chat.id}_{items[i][0]}")
        ]
        if i + 1 < len(items):
            row.append(
                InlineKeyboardButton(items[i+1][1][0], callback_data=f"genre_{message.chat.id}_{items[i+1][0]}")
            )
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{message.chat.id}")])

    await message.reply_text(
        "🎧 <b>SoundCloud Genre Explorer:</b>\n"
        "Pick a musical vibe or genre to start streaming an instant curated track:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^genre_(-?\d+)_([a-z]+)$"))
async def cb_genre_select(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    genre_key = query.matches[0].group(2)

    genre_info = GENRE_MAP.get(genre_key)
    if not genre_info:
        return await query.answer("Unknown genre!", show_alert=True)

    genre_name, search_term = genre_info
    await query.answer(f"Finding {genre_name} on SoundCloud...")

    status = await client.send_message(chat_id, f"🔍 <i>Searching top {genre_name} track on SoundCloud...</i>")
    track = await soundcloud.get_track(search_term)

    if not track or not track.get("stream_url"):
        return await status.edit_text("❌ Could not find track for this genre.")

    requester = query.from_user.mention
    track["requester_mention"] = requester
    track["requester_id"] = query.from_user.id

    is_playing = bool(queue_mgr.get_current(chat_id))

    if is_playing:
        pos = queue_mgr.add(chat_id, track)
        await status.delete()
        return await client.send_message(
            chat_id,
            f"📋 <b>Added {genre_name} to Queue</b> [#{pos}]\n"
            f"🎵 <b>Title:</b> <code>{clean_html(track['title'])}</code>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>"
        )

    try:
        await call_manager.play_or_change(chat_id, track["stream_url"])
        queue_mgr.set_current(chat_id, track)

        thumb_path = await thumbnail_gen.create_thumbnail(
            cover_url=track.get("thumbnail"),
            title=track.get("title", "Unknown"),
            artist=track.get("uploader", "SoundCloud Artist"),
            duration_sec=track.get("duration_sec", 0),
            track_id=str(track.get("id", "genre")),
        )

        caption = (
            f"🎧 <b>Genre Stream: {genre_name}</b>\n\n"
            f"🎵 <b>Title:</b> <a href=\"{track['url']}\">{clean_html(track['title'])}</a>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
            f"⏱ <b>Duration:</b> <code>{format_duration(track.get('duration_sec', 0))}</code>\n"
            f"🎧 <b>Selected by:</b> {requester}\n\n"
            f"<blockquote>⚡ <i>Curated from SoundCloud</i></blockquote>"
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
        await status.edit_text(f"❌ <b>Streaming Error:</b> <code>{e}</code>")
