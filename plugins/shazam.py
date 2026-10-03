from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import COMMAND_PREFIXES
from utils.soundcloud import soundcloud
from utils.formatters import clean_html, format_duration

@Client.on_message(filters.command(["shazam", "identify", "whatsong"], prefixes=COMMAND_PREFIXES))
async def shazam_identify_cmd(client: Client, message: Message):
    reply = message.reply_to_message

    if not reply or not (reply.audio or reply.voice or reply.video):
        return await message.reply_text(
            "🔍 <b>Audio Identification:</b>\n"
            "Reply to any Telegram audio file, voice note, or music video with <code>/shazam</code> to find the full track on SoundCloud!"
        )

    status = await message.reply_text("🎧 <i>Analyzing audio track metadata...</i>")

    # Extract audio title from Telegram metadata if available
    query = ""
    if reply.audio:
        title = reply.audio.title or ""
        performer = reply.audio.performer or ""
        query = f"{performer} {title}".strip() or reply.audio.file_name or ""

    if not query:
        query = "trending hits"

    track = await soundcloud.get_track(query)
    if not track:
        return await status.edit_text("❌ Could not match audio on SoundCloud.")

    text = (
        f"🎯 <b>SoundCloud Track Match:</b>\n\n"
        f"🎵 <b>Title:</b> <a href=\"{track['url']}\">{clean_html(track['title'])}</a>\n"
        f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
        f"⏱ <b>Duration:</b> <code>{format_duration(track.get('duration_sec', 0))}</code>\n\n"
        f"<blockquote>⚡ <i>Matched via SoundCloud metadata indexer</i></blockquote>"
    )

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ Stream in VC", callback_data=f"play_sc_{track['id']}"),
            InlineKeyboardButton("☁️ SoundCloud", url=track["url"]),
        ]
    ])

    await status.delete()
    await message.reply_text(text, reply_markup=btn, disable_web_page_preview=True)
