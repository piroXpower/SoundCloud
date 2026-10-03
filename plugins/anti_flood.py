import time
from pyrogram import Client, filters
from pyrogram.types import Message
from config import SUDO_USERS

# user_id -> timestamp of last command
LAST_ACTION = {}
COOLDOWN_SECONDS = 2.5

@Client.on_message(filters.command(["play", "sc", "stream", "song", "lyrics"], prefixes=["/", "!", ".", "?"]) & filters.group, group=-1)
async def anti_flood_check(client: Client, message: Message):
    if not message.from_user:
        return message.continue_propagation()

    user_id = message.from_user.id
    if user_id in SUDO_USERS:
        return message.continue_propagation()

    now = time.time()
    last = LAST_ACTION.get(user_id, 0)

    if now - last < COOLDOWN_SECONDS:
        message.stop_propagation()
        return await message.reply_text(
            f"⏳ <b>Slow down {message.from_user.mention}!</b>\nPlease wait a moment before sending another music command."
        )

    LAST_ACTION[user_id] = now
    message.continue_propagation()
