import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIXES
from utils.decorators import is_admin

@Client.on_message(filters.command(["clean", "purge", "clear"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def clean_cmd(client: Client, message: Message):
    if len(message.command) > 1 and message.command[1].isdigit():
        limit = min(100, max(1, int(message.command[1])))
    else:
        limit = 20

    status = await message.reply_text(f"🧹 <i>Cleaning last {limit} messages...</i>")
    chat_id = message.chat.id
    
    msg_ids = []
    async for m in client.get_chat_history(chat_id, limit=limit + 2):
        msg_ids.append(m.id)

    try:
        await client.delete_messages(chat_id, msg_ids)
        notif = await client.send_message(chat_id, f"🧹 <b>Cleaned {len(msg_ids) - 1} messages!</b>")
        await asyncio.sleep(4)
        await notif.delete()
    except Exception as e:
        await status.edit_text(f"❌ <b>Error:</b> <code>{e}</code>")
