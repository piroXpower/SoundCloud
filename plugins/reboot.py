import os
import sys
from pyrogram import Client, filters
from pyrogram.types import Message
from config import SUDO_USERS, COMMAND_PREFIXES

@Client.on_message(filters.command(["reboot", "restart"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def reboot_cmd(client: Client, message: Message):
    msg = await message.reply_text("🔄 <i>Restarting SoundCloud Music Bot...</i>")
    
    # Save message ID so bot can edit upon restart if needed
    try:
        with open("/tmp/sc_reboot.txt", "w") as f:
            f.write(f"{message.chat.id}:{msg.id}")
    except Exception:
        pass

    # Clean exit & exec
    os.execl(sys.executable, sys.executable, "main.py")
