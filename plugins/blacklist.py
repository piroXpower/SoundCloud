import os
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from config import SUDO_USERS, COMMAND_PREFIXES

BLACKLIST_FILE = "/root/SoundCloudMusicBot/blacklist.json"

def _load_blacklist() -> dict:
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"chats": [], "users": []}
    return {"chats": [], "users": []}

def _save_blacklist(data: dict):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)

@Client.on_message(filters.command(["blacklistchat", "blockchat"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def blacklist_chat_cmd(client: Client, message: Message):
    chat_id = message.chat.id if len(message.command) < 2 else int(message.command[1])
    data = _load_blacklist()

    if chat_id in data["chats"]:
        return await message.reply_text("⚠️ Chat is already blacklisted.")

    data["chats"].append(chat_id)
    _save_blacklist(data)
    await message.reply_text(f"🚫 <b>Chat Blacklisted:</b> <code>{chat_id}</code>. Music commands disabled here.")

@Client.on_message(filters.command(["whitelistchat", "unblockchat"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def whitelist_chat_cmd(client: Client, message: Message):
    chat_id = message.chat.id if len(message.command) < 2 else int(message.command[1])
    data = _load_blacklist()

    if chat_id not in data["chats"]:
        return await message.reply_text("⚠️ Chat is not in the blacklist.")

    data["chats"].remove(chat_id)
    _save_blacklist(data)
    await message.reply_text(f"✅ <b>Chat Whitelisted:</b> <code>{chat_id}</code>.")

@Client.on_message(filters.command(["blockuser", "blacklistuser"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def block_user_cmd(client: Client, message: Message):
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user.id
    elif len(message.command) > 1 and message.command[1].isdigit():
        target = int(message.command[1])

    if not target:
        return await message.reply_text("⚠️ Reply to a user or specify user ID.")

    data = _load_blacklist()
    if target in data["users"]:
        return await message.reply_text("⚠️ User is already blocked.")

    data["users"].append(target)
    _save_blacklist(data)
    await message.reply_text(f"🚫 <b>User Blocked:</b> <code>{target}</code>.")

@Client.on_message(filters.command(["unblockuser", "whitelistuser"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def unblock_user_cmd(client: Client, message: Message):
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user.id
    elif len(message.command) > 1 and message.command[1].isdigit():
        target = int(message.command[1])

    if not target:
        return await message.reply_text("⚠️ Reply to a user or specify user ID.")

    data = _load_blacklist()
    if target not in data["users"]:
        return await message.reply_text("⚠️ User is not blocked.")

    data["users"].remove(target)
    _save_blacklist(data)
    await message.reply_text(f"✅ <b>User Unblocked:</b> <code>{target}</code>.")

@Client.on_message(filters.command(["blacklisted"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def show_blacklist_cmd(client: Client, message: Message):
    data = _load_blacklist()
    text = (
        f"🚫 <b>SoundCloud Bot Blacklist:</b>\n\n"
        f"👥 <b>Blacklisted Chats ({len(data['chats'])}):</b>\n"
        f"<code>{data['chats']}</code>\n\n"
        f"👤 <b>Blocked Users ({len(data['users'])}):</b>\n"
        f"<code>{data['users']}</code>"
    )
    await message.reply_text(text)
