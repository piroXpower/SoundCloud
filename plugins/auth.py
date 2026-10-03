from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from config import COMMAND_PREFIXES
from utils.decorators import AUTH_USERS

async def is_real_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]
    except Exception:
        return False

@Client.on_message(filters.command(["auth"], prefixes=COMMAND_PREFIXES) & filters.group)
async def auth_user_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    from_user = message.from_user

    if not from_user or not await is_real_admin(client, chat_id, from_user.id):
        return await message.reply_text("❌ Only group administrators can authorize users.")

    target_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await client.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target_user:
        return await message.reply_text("⚠️ <b>Usage:</b> Reply to a user with <code>/auth</code> or <code>/auth @username</code>")

    auth_set = AUTH_USERS.setdefault(chat_id, set())
    if target_user.id in auth_set:
        return await message.reply_text(f"⚠️ {target_user.mention} is already an authorized user.")

    auth_set.add(target_user.id)
    await message.reply_text(
        f"✅ <b>User Authorized!</b>\n"
        f"👤 {target_user.mention} can now control music commands (skip, pause, volume) in this chat."
    )

@Client.on_message(filters.command(["unauth"], prefixes=COMMAND_PREFIXES) & filters.group)
async def unauth_user_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    from_user = message.from_user

    if not from_user or not await is_real_admin(client, chat_id, from_user.id):
        return await message.reply_text("❌ Only group administrators can revoke authorization.")

    target_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await client.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target_user:
        return await message.reply_text("⚠️ <b>Usage:</b> Reply to a user with <code>/unauth</code> or <code>/unauth @username</code>")

    auth_set = AUTH_USERS.get(chat_id, set())
    if target_user.id not in auth_set:
        return await message.reply_text(f"⚠️ {target_user.mention} is not in the authorized users list.")

    auth_set.remove(target_user.id)
    await message.reply_text(f"❌ <b>Authorization Revoked</b> for {target_user.mention}.")

@Client.on_message(filters.command(["authusers"], prefixes=COMMAND_PREFIXES) & filters.group)
async def list_auth_users(client: Client, message: Message):
    chat_id = message.chat.id
    auth_set = AUTH_USERS.get(chat_id, set())

    if not auth_set:
        return await message.reply_text("📋 No non-admin users have been authorized yet in this chat.")

    text = "📋 <b>Authorized Music Controllers:</b>\n\n"
    for uid in list(auth_set):
        try:
            u = await client.get_users(uid)
            text += f" • {u.mention} (<code>{uid}</code>)\n"
        except Exception:
            text += f" • <code>{uid}</code>\n"

    await message.reply_text(text)
