import os
import json
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.soundcloud import soundcloud
from utils.queue import queue_mgr
from utils.formatters import clean_html, format_duration
from core.call import call_manager
from utils.thumbnail import thumbnail_gen
from utils.inline import player_keyboard

DATA_FILE = "/root/SoundCloudMusicBot/playlists.json"

def _load_playlists() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_playlists(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@Client.on_message(filters.command(["addplaylist", "save"], prefixes=COMMAND_PREFIXES))
async def add_playlist_cmd(client: Client, message: Message):
    user_id = str(message.from_user.id)
    query = ""
    if len(message.command) > 1:
        query = " ".join(message.command[1:])
    elif message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text.strip()
    else:
        # Check current track playing in group
        curr = queue_mgr.get_current(message.chat.id)
        if curr:
            query = curr.get("url") or curr.get("title")

    if not query:
        return await message.reply_text("💾 <b>Usage:</b> <code>/addplaylist [SoundCloud URL or Track Name]</code>")

    status = await message.reply_text("🔍 <i>Fetching track details for playlist...</i>")
    track = await soundcloud.get_track(query)

    if not track:
        return await status.edit_text("❌ Track not found on SoundCloud.")

    data = _load_playlists()
    user_pl = data.setdefault(user_id, [])

    if len(user_pl) >= 50:
        return await status.edit_text("⚠️ Playlist limit reached (maximum 50 tracks).")

    # Check if duplicate
    for t in user_pl:
        if t.get("url") == track.get("url"):
            return await status.edit_text("⚠️ Track is already in your playlist!")

    user_pl.append({
        "title": track["title"],
        "uploader": track["uploader"],
        "url": track["url"],
        "duration_sec": track.get("duration_sec", 0),
        "id": track.get("id"),
    })
    _save_playlists(data)

    await status.edit_text(
        f"✅ <b>Added to your Playlist:</b>\n"
        f"🎵 <b>Title:</b> <code>{clean_html(track['title'])}</code>\n"
        f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
        f"🔢 <b>Total saved tracks:</b> <code>{len(user_pl)}</code>"
    )

@Client.on_message(filters.command(["playlist", "myplaylist"], prefixes=COMMAND_PREFIXES))
async def view_playlist_cmd(client: Client, message: Message):
    user_id = str(message.from_user.id)
    data = _load_playlists()
    user_pl = data.get(user_id, [])

    if not user_pl:
        return await message.reply_text(
            "📂 <b>Your SoundCloud Playlist is empty!</b>\n\n"
            "Use <code>/addplaylist [track]</code> or save what's currently playing."
        )

    text = f"📂 <b>Your Saved SoundCloud Playlist ({len(user_pl)} tracks):</b>\n\n"
    for i, t in enumerate(user_pl[:15], start=1):
        dur = format_duration(t.get("duration_sec", 0))
        text += f"<b>{i}.</b> <a href=\"{t['url']}\">{clean_html(t['title'])}</a> (<code>{dur}</code>)\n"

    if len(user_pl) > 15:
        text += f"\n<i>...and {len(user_pl) - 15} more tracks.</i>"

    buttons = [
        [
            InlineKeyboardButton("▶️ Play Entire Playlist", callback_data=f"pl_play_{user_id}"),
            InlineKeyboardButton("🗑 Clear All", callback_data=f"pl_clear_{user_id}"),
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="pl_close"),
        ]
    ]

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Client.on_message(filters.command(["delplaylist", "removeplaylist"], prefixes=COMMAND_PREFIXES))
async def del_playlist_cmd(client: Client, message: Message):
    user_id = str(message.from_user.id)
    if len(message.command) < 2:
        return await message.reply_text("🗑 <b>Usage:</b> <code>/delplaylist [position number]</code>")

    try:
        idx = int(message.command[1]) - 1
    except ValueError:
        return await message.reply_text("❌ Please enter a valid number.")

    data = _load_playlists()
    user_pl = data.get(user_id, [])

    if not 0 <= idx < len(user_pl):
        return await message.reply_text("❌ Invalid track number.")

    removed = user_pl.pop(idx)
    _save_playlists(data)

    await message.reply_text(f"🗑 Removed <b>{clean_html(removed['title'])}</b> from your playlist.")

@Client.on_callback_query(filters.regex(r"^pl_play_(\d+)$"))
async def cb_play_playlist(client: Client, query: CallbackQuery):
    user_id = query.matches[0].group(1)
    chat_id = query.message.chat.id

    if str(query.from_user.id) != user_id:
        return await query.answer("⚠️ This is not your playlist!", show_alert=True)

    if query.message.chat.type.name not in ["GROUP", "SUPERGROUP"]:
        return await query.answer("⚠️ Playlists can only be streamed inside groups with voice chat!", show_alert=True)

    data = _load_playlists()
    user_pl = data.get(user_id, [])

    if not user_pl:
        return await query.answer("Playlist is empty!", show_alert=True)

    await query.answer("🔄 Queueing playlist tracks...")
    status = await client.send_message(chat_id, f"📂 <b>Loading {len(user_pl)} tracks from playlist...</b>")

    added = 0
    first_track = None

    for item in user_pl:
        t = await soundcloud.get_track(item["url"])
        if not t or not t.get("stream_url"):
            continue

        t["requester_mention"] = query.from_user.mention
        t["requester_id"] = query.from_user.id

        if not queue_mgr.get_current(chat_id) and first_track is None:
            first_track = t
        else:
            queue_mgr.add(chat_id, t)
        added += 1

    if first_track:
        try:
            await call_manager.play_or_change(chat_id, first_track["stream_url"])
            queue_mgr.set_current(chat_id, first_track)

            thumb_path = await thumbnail_gen.create_thumbnail(
                cover_url=first_track.get("thumbnail"),
                title=first_track.get("title", "Unknown"),
                artist=first_track.get("uploader", "SoundCloud Artist"),
                duration_sec=first_track.get("duration_sec", 0),
                track_id=str(first_track.get("id", "pl")),
            )

            dur_str = format_duration(first_track.get("duration_sec", 0))
            caption = (
                f"☁️ <b>Started Playlist Playback:</b>\n\n"
                f"🎵 <b>Now Playing:</b> <a href=\"{first_track['url']}\">{clean_html(first_track['title'])}</a>\n"
                f"👤 <b>Artist:</b> <code>{clean_html(first_track['uploader'])}</code>\n"
                f"⏱ <b>Duration:</b> <code>{dur_str}</code>\n"
                f"🎧 <b>Queued:</b> <code>{added}</code> tracks from {query.from_user.mention}'s playlist\n\n"
                f"<blockquote>⚡ <i>Streamed via PyTgCalls</i></blockquote>"
            )

            keyboard = player_keyboard(
                chat_id=chat_id,
                is_paused=False,
                loop_mode=queue_mgr.get_loop(chat_id),
                sc_url=first_track.get("url", ""),
            )

            await status.delete()
            await client.send_photo(chat_id, photo=thumb_path, caption=caption, reply_markup=keyboard)
            return

        except Exception as e:
            await status.edit_text(f"❌ <b>Error starting playback:</b> <code>{clean_html(str(e))}</code>")
            return

    await status.edit_text(f"✅ Queued <b>{added}</b> tracks from playlist into the voice chat queue!")

@Client.on_callback_query(filters.regex(r"^pl_clear_(\d+)$"))
async def cb_clear_user_playlist(client: Client, query: CallbackQuery):
    user_id = query.matches[0].group(1)
    if str(query.from_user.id) != user_id:
        return await query.answer("⚠️ Not your playlist!", show_alert=True)

    data = _load_playlists()
    data.pop(user_id, None)
    _save_playlists(data)

    await query.answer("🧹 Playlist cleared!")
    await query.message.edit_text("📂 <b>Your saved SoundCloud playlist has been cleared.</b>")

@Client.on_callback_query(filters.regex("^pl_close$"))
async def cb_close_pl(client: Client, query: CallbackQuery):
    await query.message.delete()
