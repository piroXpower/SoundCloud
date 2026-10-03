from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.queue import queue_mgr
from utils.formatters import clean_html, format_duration
from utils.soundcloud import soundcloud
from core.call import call_manager
from utils.thumbnail import thumbnail_gen
from utils.inline import player_keyboard

@Client.on_message(filters.command(["history", "recent"], prefixes=COMMAND_PREFIXES) & filters.group)
async def history_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    history = queue_mgr.get_history(chat_id)

    if not history:
        return await message.reply_text("📜 <b>Playback History is empty!</b> No tracks have been played yet in this chat.")

    text = "🕒 <b>Recently Streamed SoundCloud Tracks:</b>\n\n"
    buttons = []
    
    # We display up to 8 recent tracks with replay buttons
    for idx, track in enumerate(history[:8]):
        dur = format_duration(track.get("duration_sec", 0))
        text += f"<b>{idx + 1}.</b> <a href=\"{track['url']}\">{clean_html(track['title'])}</a> (<code>{dur}</code>)\n"
        text += f"    👤 <i>{clean_html(track['uploader'])}</i>\n\n"

    # Row of replay buttons
    row1 = [InlineKeyboardButton(f"▶️ #{i+1}", callback_data=f"hist_play_{chat_id}_{i}") for i in range(min(4, len(history[:8])))]
    buttons.append(row1)

    if len(history[:8]) > 4:
        row2 = [InlineKeyboardButton(f"▶️ #{i+1}", callback_data=f"hist_play_{chat_id}_{i}") for i in range(4, len(history[:8]))]
        buttons.append(row2)

    buttons.append([InlineKeyboardButton("🗑 Close", callback_data="hist_close")])

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Client.on_callback_query(filters.regex(r"^hist_play_(-?\d+)_(\d+)$"))
async def cb_replay_history(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    idx = int(query.matches[0].group(2))

    history = queue_mgr.get_history(chat_id)
    if not history or idx >= len(history):
        return await query.answer("Track no longer available in history.", show_alert=True)

    item = history[idx]
    await query.answer(f"Queueing: {item['title'][:20]}...")

    status = await client.send_message(chat_id, f"🔄 <i>Replaying:</i> <b>{clean_html(item['title'])}</b>...")
    track = await soundcloud.get_track(item["url"])

    if not track or not track.get("stream_url"):
        return await status.edit_text("❌ Failed to resolve audio stream for track.")

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
            f"🎧 <b>Replayed by:</b> {requester}"
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
            track_id=str(track.get("id", "hist")),
        )

        caption = (
            f"☁️ <b>Now Streaming on SoundCloud:</b>\n\n"
            f"🎵 <b>Title:</b> <a href=\"{track['url']}\">{clean_html(track['title'])}</a>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
            f"⏱ <b>Duration:</b> <code>{format_duration(track.get('duration_sec', 0))}</code>\n"
            f"🎧 <b>Replayed by:</b> {requester}\n\n"
            f"<blockquote>⚡ <i>Crystal-clear 320kbps audio directly from SoundCloud</i></blockquote>"
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

@Client.on_callback_query(filters.regex("^hist_close$"))
async def cb_close_history(client: Client, query: CallbackQuery):
    await query.message.delete()
