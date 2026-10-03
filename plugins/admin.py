from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIXES
from utils.decorators import is_admin
from utils.queue import queue_mgr
from utils.formatters import format_duration, clean_html
from utils.inline import player_keyboard
from core.call import call_manager

@Client.on_message(filters.command(["pause"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def pause_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if not queue_mgr.get_current(chat_id):
        return await message.reply_text("❌ Nothing is currently streaming.")
    
    if queue_mgr.is_paused(chat_id):
        return await message.reply_text("⚠️ Playback is already paused.")

    await call_manager.pause(chat_id)
    await message.reply_text("⏸ <b>SoundCloud Stream Paused!</b>\nUse <code>/resume</code> to continue.")

@Client.on_message(filters.command(["resume"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def resume_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if not queue_mgr.get_current(chat_id):
        return await message.reply_text("❌ Nothing is currently streaming.")

    if not queue_mgr.is_paused(chat_id):
        return await message.reply_text("⚠️ Stream is already playing.")

    await call_manager.resume(chat_id)
    await message.reply_text("▶️ <b>SoundCloud Stream Resumed!</b>")

@Client.on_message(filters.command(["skip", "next"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def skip_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if not queue_mgr.get_current(chat_id):
        return await message.reply_text("❌ Nothing is currently streaming.")

    msg = await message.reply_text("⏭ <i>Skipping to the next track...</i>")
    await call_manager._on_stream_end(chat_id)
    await msg.delete()

@Client.on_message(filters.command(["stop", "end", "leave"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def stop_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    await call_manager.stop(chat_id)
    await message.reply_text("🛑 <b>SoundCloud Stream Stopped!</b>\nVoice chat connection closed & queue cleared.")

@Client.on_message(filters.command(["loop"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def loop_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg in ["track", "song", "single"]:
            queue_mgr._loop[chat_id] = "track"
        elif arg in ["queue", "all"]:
            queue_mgr._loop[chat_id] = "queue"
        elif arg in ["off", "disable", "stop"]:
            queue_mgr._loop[chat_id] = "none"
        mode = queue_mgr.get_loop(chat_id)
    else:
        mode = queue_mgr.toggle_loop(chat_id)

    status_str = "Disabled" if mode == "none" else f"Enabled ({mode.capitalize()})"
    await message.reply_text(f"🔁 <b>Loop Mode:</b> <code>{status_str}</code>")

@Client.on_message(filters.command(["volume", "vol"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def volume_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        curr_vol = queue_mgr.get_volume(chat_id)
        return await message.reply_text(f"🔊 <b>Current Volume:</b> <code>{curr_vol}%</code>\nUsage: <code>/volume 1-200</code>")

    try:
        vol = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Please enter a valid number between 1 and 200.")

    if not 1 <= vol <= 200:
        return await message.reply_text("❌ Volume must be between <code>1</code> and <code>200</code>.")

    await call_manager.set_volume(chat_id, vol)
    await message.reply_text(f"🔊 <b>Volume changed to:</b> <code>{vol}%</code>")

@Client.on_message(filters.command(["mute"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def mute_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    await call_manager.mute(chat_id)
    await message.reply_text("🔇 <b>Assistant Muted in Voice Chat.</b>")

@Client.on_message(filters.command(["unmute"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def unmute_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    await call_manager.unmute(chat_id)
    await message.reply_text("🔊 <b>Assistant Unmuted in Voice Chat.</b>")

@Client.on_message(filters.command(["queue", "q"], prefixes=COMMAND_PREFIXES) & filters.group)
async def queue_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)
    tracks = queue_mgr.get_queue(chat_id)

    if not curr and not tracks:
        return await message.reply_text("📜 SoundCloud Queue is currently empty.")

    text = "📜 <b>SoundCloud Up Next Queue:</b>\n\n"
    if curr:
        text += f"🎧 <b>Now Playing:</b>\n └ <code>{clean_html(curr['title'])}</code> ({format_duration(curr.get('duration_sec', 0))})\n\n"

    if tracks:
        text += "📋 <b>Upcoming in Queue:</b>\n"
        for i, tr in enumerate(tracks[:10], start=1):
            text += f" <b>{i}.</b> <code>{clean_html(tr['title'])}</code> ({format_duration(tr.get('duration_sec', 0))})\n"
        if len(tracks) > 10:
            text += f"\n<i>...and {len(tracks) - 10} more tracks.</i>\n"
    else:
        text += "<i>No other tracks pending in queue.</i>\n"

    await message.reply_text(text)

@Client.on_message(filters.command(["clearqueue"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def clear_queue_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    queue_mgr.get_queue(chat_id).clear()
    await message.reply_text("🧹 <b>SoundCloud Queue Cleared Successfully!</b>")
