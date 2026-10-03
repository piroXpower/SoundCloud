from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIXES
from utils.soundcloud import soundcloud
from core.call import call_manager
from utils.queue import queue_mgr
from utils.formatters import clean_html, format_duration

@Client.on_message(filters.command(["cplay", "channelplay"], prefixes=COMMAND_PREFIXES))
async def channel_play_cmd(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text(
            "📢 <b>Channel Playback Usage:</b>\n"
            "<code>/cplay [channel_username or channel_id] [track name or link]</code>\n\n"
            "Example: <code>/cplay @mychannel Alan Walker Faded</code>"
        )

    channel_target = message.command[1].strip()
    query = " ".join(message.command[2:])

    try:
        chat = await client.get_chat(channel_target)
    except Exception as e:
        return await message.reply_text(f"❌ Failed to locate channel: <code>{e}</code>")

    status = await message.reply_text(f"🔍 <i>Searching SoundCloud for channel stream:</i> <code>{clean_html(query)}</code>...")
    track = await soundcloud.get_track(query)

    if not track or not track.get("stream_url"):
        return await status.edit_text("❌ Track not found on SoundCloud.")

    try:
        await status.edit_text(f"🔄 <i>Connecting to Channel Voice Chat:</i> <b>{chat.title}</b>...")
        await call_manager.play_or_change(chat.id, track["stream_url"])
        queue_mgr.set_current(chat.id, track)

        dur_str = format_duration(track.get("duration_sec", 0))
        await status.edit_text(
            f"📢 <b>Now Streaming in Channel:</b>\n\n"
            f"📡 <b>Channel:</b> <code>{chat.title}</code>\n"
            f"🎵 <b>Title:</b> <a href=\"{track['url']}\">{clean_html(track['title'])}</a>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(track['uploader'])}</code>\n"
            f"⏱ <b>Duration:</b> <code>{dur_str}</code>\n"
            f"🎧 <b>Started by:</b> {message.from_user.mention}"
        )
    except Exception as e:
        await status.edit_text(f"❌ <b>Channel Streaming Error:</b> <code>{clean_html(str(e))}</code>")

@Client.on_message(filters.command(["cstop", "channelstop"], prefixes=COMMAND_PREFIXES))
async def channel_stop_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("📢 <b>Usage:</b> <code>/cstop [channel_id or username]</code>")

    target = message.command[1].strip()
    try:
        chat = await client.get_chat(target)
        await call_manager.stop(chat.id)
        await message.reply_text(f"🛑 <b>Stopped streaming in channel:</b> <code>{chat.title}</code>")
    except Exception as e:
        await message.reply_text(f"❌ <b>Error:</b> <code>{e}</code>")
