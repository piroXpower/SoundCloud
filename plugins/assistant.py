import time
from pyrogram import Client, filters
from pyrogram.types import Message

from config import COMMAND_PREFIXES
from core.assistant import userbot
from utils.decorators import is_admin

@Client.on_message(filters.command(["userbotjoin", "assistantjoin"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def join_assistant_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    status = await message.reply_text("🔄 <i>Inviting assistant userbot to group...</i>")

    try:
        # Export group invite link
        link = await client.export_chat_invite_link(chat_id)
        # Assistant joins group
        await userbot.join_chat(link)
        await status.edit_text("✅ <b>Assistant userbot joined successfully!</b> Ready to stream in voice chat.")
    except Exception as e:
        await status.edit_text(f"❌ <b>Failed to join:</b> <code>{e}</code>\nMake sure the bot has permission to invite users!")

@Client.on_message(filters.command(["userbotleave", "assistantleave"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def leave_assistant_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    try:
        await userbot.leave_chat(chat_id)
        await message.reply_text("👋 <b>Assistant userbot left the chat.</b>")
    except Exception as e:
        await message.reply_text(f"❌ <b>Error:</b> <code>{e}</code>")

@Client.on_message(filters.command(["assistantstatus", "assstatus"], prefixes=COMMAND_PREFIXES))
async def assistant_status_cmd(client: Client, message: Message):
    start = time.time()
    try:
        me = await userbot.get_me()
        latency = round((time.time() - start) * 1000, 2)
        text = (
            f"🎙️ <b>PyTgCalls Assistant Status:</b>\n\n"
            f"👤 <b>Name:</b> {me.first_name}\n"
            f"📛 <b>Username:</b> @{me.username or 'None'}\n"
            f"🏷 <b>User ID:</b> <code>{me.id}</code>\n"
            f"📶 <b>Ping Latency:</b> <code>{latency} ms</code>\n"
            f"🟢 <b>Status:</b> <code>Online & Ready</code>"
        )
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"❌ <b>Assistant Offline / Error:</b> <code>{e}</code>")
