from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIXES
from utils.decorators import is_admin

# chat_id -> bool
DJ_MODE_STATE = {}

def is_dj_enabled(chat_id: int) -> bool:
    return DJ_MODE_STATE.get(chat_id, False)

@Client.on_message(filters.command(["djmode", "dj"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def toggle_dj_mode(client: Client, message: Message):
    chat_id = message.chat.id

    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg in ["on", "enable", "yes", "true"]:
            DJ_MODE_STATE[chat_id] = True
        elif arg in ["off", "disable", "no", "false"]:
            DJ_MODE_STATE[chat_id] = False
        else:
            return await message.reply_text("⚠️ <b>Usage:</b> <code>/djmode [on / off]</code>")
    else:
        # Toggle
        current = DJ_MODE_STATE.get(chat_id, False)
        DJ_MODE_STATE[chat_id] = not current

    state = DJ_MODE_STATE[chat_id]
    if state:
        await message.reply_text(
            "🎧 <b>DJ Mode Enabled!</b>\n\n"
            "Only group administrators and authorized users can add songs to the queue or control playback."
        )
    else:
        await message.reply_text(
            "🎧 <b>DJ Mode Disabled!</b>\n\n"
            "All group members can now request songs from SoundCloud."
        )
