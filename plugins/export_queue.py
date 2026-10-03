import os
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIXES
from utils.queue import queue_mgr
from utils.formatters import clean_html

@Client.on_message(filters.command(["exportqueue", "exportq"], prefixes=COMMAND_PREFIXES) & filters.group)
async def export_queue_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)
    tracks = queue_mgr.get_queue(chat_id)

    if not curr and not tracks:
        return await message.reply_text("📜 SoundCloud queue is currently empty. Nothing to export.")

    all_tracks = []
    if curr:
        all_tracks.append(curr)
    all_tracks.extend(tracks)

    # Generate M3U playlist file content
    m3u_lines = ["#EXTM3U\n"]
    for t in all_tracks:
        dur = t.get("duration_sec", 0)
        title = t.get("title", "Unknown")
        uploader = t.get("uploader", "SoundCloud Artist")
        url = t.get("url", "")
        m3u_lines.append(f"#EXTINF:{dur},{uploader} - {title}\n{url}\n")

    export_path = f"/tmp/queue_{chat_id}.m3u"
    with open(export_path, "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)

    await message.reply_document(
        document=export_path,
        caption=(
            f"📜 <b>Exported SoundCloud Queue:</b>\n"
            f"• Total tracks: <code>{len(all_tracks)}</code>\n"
            f"• Format: <code>.M3U Playlist</code>"
        )
    )

    if os.path.exists(export_path):
        try:
            os.remove(export_path)
        except Exception:
            pass
