import os
import sys
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import sudo_only


@bot.on_message(filters.command(["restart", "reboot"]) & sudo_only)
async def restart_command(_, message: types.Message):
    msg = await message.reply_text("🔄 <b>Restarting bot process...</b> Please wait a few seconds.")
    try:
        # Save restart message context if needed
        await db._db.system.update_one(
            {"_id": "restart"},
            {"$set": {"chat_id": message.chat.id, "message_id": msg.id}},
            upsert=True
        )
    except Exception:
        pass

    os.execl(sys.executable, sys.executable, "-m", "maxmusic")
