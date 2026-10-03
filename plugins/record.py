import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import subprocess

from config import COMMAND_PREFIXES
from utils.decorators import is_admin
from utils.queue import queue_mgr
from utils.formatters import clean_html

@Client.on_message(filters.command(["record", "vcrecord"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def record_stream_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)

    if not curr or not curr.get("stream_url"):
        return await message.reply_text("❌ Nothing is currently streaming to record.")

    duration = 30 # default 30 seconds
    if len(message.command) > 1 and message.command[1].isdigit():
        duration = min(120, max(5, int(message.command[1])))

    status = await message.reply_text(f"🎙️ <i>Recording {duration} seconds of current stream...</i>")

    record_path = f"/tmp/record_{chat_id}.mp3"
    stream_url = curr["stream_url"]

    # Use ffmpeg to record audio snippet directly from the stream url
    cmd = [
        "ffmpeg",
        "-y",
        "-t", str(duration),
        "-i", stream_url,
        "-acodec", "libmp3lame",
        "-ab", "192k",
        record_path
    ]

    try:
        proc = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, timeout=duration + 15)
        if not os.path.exists(record_path):
            return await status.edit_text("❌ Failed to record audio snippet.")

        await status.edit_text("📤 <i>Uploading voice recording to Telegram...</i>")
        await message.reply_voice(
            voice=record_path,
            caption=(
                f"🎙️ <b>Recorded Audio Clip ({duration}s):</b>\n"
                f"🎵 <code>{clean_html(curr['title'])}</code>"
            )
        )
        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ <b>Recording Error:</b> <code>{clean_html(str(e))}</code>")
    finally:
        if os.path.exists(record_path):
            try:
                os.remove(record_path)
            except Exception:
                pass
