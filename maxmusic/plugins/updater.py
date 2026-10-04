import os
import sys
import subprocess
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.filters import owner_only


@bot.on_message(filters.command(["update"]) & owner_only)
async def update_command(_, message: types.Message):
    status_msg = await message.reply_text("🔄 <i>Checking for Git updates...</i>")
    try:
        proc = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        output = (out or "") + (err or "")

        if "Already up to date." in output:
            return await status_msg.edit_text("✅ <b>Bot is already up to date with Git repository!</b>")

        await status_msg.edit_text(
            f"📥 <b>Updated Successfully:</b>\n<pre>{output[:1000]}</pre>\n\nRestarting bot process..."
        )
        os.execl(sys.executable, sys.executable, "-m", "maxmusic")
    except Exception as e:
        await status_msg.edit_text(f"❌ Update failed: {e}")
