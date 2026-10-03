import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import COMMAND_PREFIXES, DURATION_LIMIT_MINUTES
from utils.soundcloud import soundcloud
from utils.thumbnail import thumbnail_gen
from utils.queue import queue_mgr
from utils.inline import player_keyboard
from utils.formatters import format_duration, clean_html
from core.call import call_manager

@Client.on_message(filters.command(["play", "sc", "stream"], prefixes=COMMAND_PREFIXES))
async def play_handler(client: Client, message: Message):
    chat_id = message.chat.id

    # Music streaming is meant for groups and channels
    if message.chat.type.name not in ["GROUP", "SUPERGROUP", "CHANNEL"]:
        return await message.reply_text(
            "⚠️ <b>Voice Chat Streaming</b> is only supported in Groups and Supergroups!\n\n"
            "👉 Please add me to your group and start a voice chat."
        )

    # Extract query
    query = ""
    if len(message.command) > 1:
        query = " ".join(message.command[1:])
    elif message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text.strip()

    if not query:
        return await message.reply_text(
            "☁️ <b>Usage:</b>\n"
            "• <code>/play [SoundCloud URL or Song Name]</code>\n"
            "• Example: <code>/play Alan Walker Faded remix</code>\n"
            "• Example: <code>/play https://soundcloud.com/user/track</code>"
        )

    # Service message: Searching
    status_msg = await message.reply_text(
        "🔍 <b>Searching SoundCloud for your track...</b>\n"
        "⚡ <i>Fetching high-fidelity audio stream</i>"
    )

    try:
        track = await soundcloud.get_track(query)
    except Exception as e:
        return await status_msg.edit_text(f"❌ <b>Extraction Error:</b> <code>{clean_html(str(e))}</code>")

    if not track or not track.get("stream_url"):
        return await status_msg.edit_text(
            "❌ <b>Track Not Found on SoundCloud!</b>\n"
            "Please ensure the track is public, or try searching with artist and title."
        )

    # Check track duration limit
    duration_sec = track.get("duration_sec", 0)
    if duration_sec > (DURATION_LIMIT_MINUTES * 60):
        return await status_msg.edit_text(
            f"⚠️ <b>Duration Limit Exceeded!</b>\n"
            f"Tracks longer than {DURATION_LIMIT_MINUTES} minutes are not allowed."
        )

    # User mention
    requester = message.from_user.mention if message.from_user else "Anonymous"
    track["requester_mention"] = requester
    track["requester_id"] = message.from_user.id if message.from_user else 0

    is_currently_playing = bool(queue_mgr.get_current(chat_id))

    # Case 1: Already playing -> Add to queue
    if is_currently_playing:
        pos = queue_mgr.add(chat_id, track)
        dur_str = format_duration(duration_sec)
        
        queue_text = (
            f"📋 <b>Track Added to SoundCloud Queue</b> [#{pos}]\n\n"
            f"🎵 <b>Title:</b> <a href=\"{track['url']}\">{clean_html(track['title'])}</a>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
            f"⏱ <b>Duration:</b> <code>{dur_str}</code>\n"
            f"🎧 <b>Requested by:</b> {requester}\n\n"
            f"<blockquote>⚡ <i>Will play automatically when current tracks finish.</i></blockquote>"
        )
        
        btn = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📜 View Queue", callback_data=f"ctrl_queue_{chat_id}_0"),
                InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}"),
            ]
        ])
        await status_msg.delete()
        return await message.reply_text(queue_text, reply_markup=btn, disable_web_page_preview=True)

    # Case 2: Nothing playing -> Start streaming now
    try:
        await status_msg.edit_text("🔄 <b>Connecting to Group Voice Chat...</b>")
        
        # Connect & stream via PyTgCalls
        await call_manager.play_or_change(chat_id, track["stream_url"])
        queue_mgr.set_current(chat_id, track)

        # Generate awesome thumbnail card in background
        await status_msg.edit_text("🎨 <b>Generating HD Album Art...</b>")
        thumb_path = await thumbnail_gen.create_thumbnail(
            cover_url=track.get("thumbnail"),
            title=track.get("title", "Unknown"),
            artist=track.get("uploader", "SoundCloud Artist"),
            duration_sec=duration_sec,
            track_id=str(track.get("id", "now")),
        )

        dur_str = format_duration(duration_sec)
        caption = (
            f"☁️ <b>Now Streaming on SoundCloud:</b>\n\n"
            f"🎵 <b>Title:</b> <a href=\"{track['url']}\">{clean_html(track['title'])}</a>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
            f"⏱ <b>Duration:</b> <code>{dur_str}</code>\n"
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

        if os.path.exists(thumb_path):
            await message.reply_photo(
                photo=thumb_path,
                caption=caption,
                reply_markup=keyboard,
            )
        else:
            await message.reply_text(
                caption,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )

    except Exception as e:
        await status_msg.edit_text(
            f"❌ <b>Streaming Error:</b> <code>{clean_html(str(e))}</code>\n\n"
            f"<i>Make sure the assistant account has joined the group and the voice chat is active!</i>"
        )
