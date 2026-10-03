from pyrogram import Client, filters
from pyrogram.types import Message

from config import COMMAND_PREFIXES
from utils.decorators import is_admin
from utils.queue import queue_mgr
from utils.formatters import format_duration
from core.call import call_manager

def parse_time(time_str: str) -> int:
    try:
        parts = time_str.split(":")
        if len(parts) == 1:
            return int(parts[0])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return -1
    return -1

@Client.on_message(filters.command(["seek", "jump"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def seek_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)

    if not curr:
        return await message.reply_text("❌ Nothing is currently streaming.")

    if len(message.command) < 2:
        return await message.reply_text(
            "⏩ <b>Usage:</b> <code>/seek [seconds or MM:SS]</code>\n"
            "Example: <code>/seek 45</code> or <code>/seek 01:20</code>"
        )

    time_arg = message.command[1].strip()
    seconds = parse_time(time_arg)

    if seconds < 0:
        return await message.reply_text("❌ Invalid time format! Use seconds (e.g. <code>60</code>) or <code>01:30</code>.")

    total_sec = curr.get("duration_sec", 0)
    if total_sec > 0 and seconds >= total_sec:
        return await message.reply_text(f"⚠️ Target time exceeds track duration ({format_duration(total_sec)}).")

    msg = await message.reply_text(f"⏩ <i>Seeking stream to {format_duration(seconds)}...</i>")

    try:
        # Seek stream by restarting with ffmpeg offset
        base_url = curr["stream_url"]
        seek_stream_url = f"{base_url}#t={seconds}" if "#" not in base_url else base_url
        await call_manager.play_or_change(chat_id, seek_stream_url)
        await msg.edit_text(f"⏩ <b>Playback Seeked!</b>\nNow streaming from: <code>{format_duration(seconds)}</code>")
    except Exception as e:
        await msg.edit_text(f"❌ <b>Seek Error:</b> <code>{e}</code>")
