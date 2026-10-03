import random
from pyrogram import Client, filters
from pyrogram.types import Message

from config import COMMAND_PREFIXES
from utils.queue import queue_mgr
from utils.decorators import is_admin

@Client.on_message(filters.command(["shuffle"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def shuffle_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    queue = queue_mgr.get_queue(chat_id)

    if not queue or len(queue) < 2:
        return await message.reply_text("⚠️ Need at least 2 tracks in the queue to shuffle.")

    random.shuffle(queue)
    await message.reply_text(
        f"🔀 <b>SoundCloud Queue Shuffled!</b>\n"
        f"Randomized <code>{len(queue)}</code> tracks in queue.\n"
        f"Use <code>/queue</code> to view the new order."
    )
