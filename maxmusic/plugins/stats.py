import time
import psutil
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.formatters import get_readable_time, get_readable_bytes
from maxmusic.config import config

BOT_START_TIME = time.time()


@bot.on_message(filters.command(["stats", "gstats", "botstats"]))
async def stats_command(_, message: types.Message):
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    cpu_percent = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    active_vc = len(db.active_calls)
    total_chats = await db._db.chats.count_documents({})
    total_users = await db._db.users.count_documents({})
    sudo_count = len(db.sudoers)

    text = (
        f"📊 <b>{config.BOT_NAME} System Statistics</b>\n\n"
        f"⏱ <b>Uptime:</b> {uptime}\n"
        f"🖥 <b>CPU Usage:</b> {cpu_percent}%\n"
        f"🧠 <b>RAM Usage:</b> {ram.percent}% ({get_readable_bytes(ram.used)} / {get_readable_bytes(ram.total)})\n"
        f"💾 <b>Disk Usage:</b> {disk.percent}% ({get_readable_bytes(disk.used)} / {get_readable_bytes(disk.total)})\n\n"
        f"📈 <b>Bot Statistics:</b>\n"
        f"• <b>Active Voice Chats:</b> {active_vc}\n"
        f"• <b>Total Served Chats:</b> {total_chats}\n"
        f"• <b>Total Users:</b> {total_users}\n"
        f"• <b>Sudo Users:</b> {sudo_count}\n"
    )

    await message.reply_text(text)
