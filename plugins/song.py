import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp

from config import COMMAND_PREFIXES
from utils.soundcloud import soundcloud
from utils.formatters import clean_html, format_duration

DOWNLOAD_DIR = "/tmp/sc_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def _download_track(url: str, output_template: str) -> dict:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info

@Client.on_message(filters.command(["song", "download", "dl"], prefixes=COMMAND_PREFIXES))
async def download_song_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text(
            "📥 <b>Usage:</b> <code>/song [SoundCloud URL or Track Name]</code>\n"
            "Example: <code>/song Martin Garrix Animals</code>"
        )

    query = " ".join(message.command[1:]) if len(message.command) > 1 else message.reply_to_message.text.strip()
    status = await message.reply_text("🔍 <i>Searching SoundCloud for download...</i>")

    track = await soundcloud.get_track(query)
    if not track or not track.get("url"):
        return await status.edit_text("❌ Could not find track on SoundCloud.")

    await status.edit_text(f"⏳ <b>Downloading & Encoding:</b> <code>{clean_html(track['title'])}</code> (320kbps MP3)...")

    file_prefix = f"sc_{track.get('id', 'dl')}"
    raw_template = os.path.join(DOWNLOAD_DIR, f"{file_prefix}.%(ext)s")
    final_file = os.path.join(DOWNLOAD_DIR, f"{file_prefix}.mp3")

    try:
        await asyncio.to_thread(_download_track, track["url"], raw_template)
        if not os.path.exists(final_file):
            return await status.edit_text("❌ Failed to process audio file.")

        await status.edit_text("📤 <i>Uploading high-res audio to Telegram...</i>")

        caption = (
            f"☁️ <b>Downloaded from SoundCloud:</b>\n\n"
            f"🎵 <b>Title:</b> {clean_html(track['title'])}\n"
            f"👤 <b>Artist:</b> {clean_html(track['uploader'])}\n"
            f"⏱ <b>Duration:</b> {format_duration(track.get('duration_sec', 0))}\n"
            f"🎧 <b>Source:</b> <a href=\"{track['url']}\">SoundCloud Link</a>"
        )

        await message.reply_audio(
            audio=final_file,
            caption=caption,
            title=track["title"],
            performer=track["uploader"],
            duration=track.get("duration_sec", 0),
        )
        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ <b>Download Error:</b> <code>{clean_html(str(e))}</code>")
    finally:
        if os.path.exists(final_file):
            try:
                os.remove(final_file)
            except Exception:
                pass
