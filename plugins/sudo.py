import os
import psutil
from pyrogram import Client, filters
from pyrogram.types import Message
from config import SUDO_USERS, COMMAND_PREFIXES
from utils.formatters import humanbytes
from utils.queue import queue_mgr

@Client.on_message(filters.command(["stats"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def stats_cmd(client: Client, message: Message):
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    active_streams = len([c for c, q in queue_mgr._current.items() if q])
    total_queued = sum(len(q) for q in queue_mgr._queues.values())

    stats_text = (
        f"📊 <b>SoundCloud Bot System Stats</b> 🚀\n\n"
        f"💻 <b>CPU Usage:</b> <code>{cpu}%</code>\n"
        f"🧠 <b>RAM Usage:</b> <code>{humanbytes(mem.used)} / {humanbytes(mem.total)} ({mem.percent}%)</code>\n"
        f"💾 <b>Disk Usage:</b> <code>{humanbytes(disk.used)} / {humanbytes(disk.total)} ({disk.percent}%)</code>\n\n"
        f"🎙️ <b>Active Voice Chats:</b> <code>{active_streams}</code>\n"
        f"📜 <b>Total Queued Tracks:</b> <code>{total_queued}</code>\n"
    )
    await message.reply_text(stats_text)

@Client.on_message(filters.command(["broadcast", "bcast"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def broadcast_cmd(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a message to broadcast it.")

    msg = await message.reply_text("📢 <i>Broadcasting message in background...</i>")
    success = 0
    failed = 0

    # Get all dialogs
    async for dialog in client.get_dialogs():
        try:
            await message.reply_to_message.copy(chat_id=dialog.chat.id)
            success += 1
        except Exception:
            failed += 1

    await msg.edit_text(
        f"✅ <b>Broadcast Completed!</b>\n\n"
        f"• Sent to: <code>{success}</code> chats\n"
        f"• Failed in: <code>{failed}</code> chats"
    )
