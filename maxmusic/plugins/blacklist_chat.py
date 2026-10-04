from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import sudo_only


@bot.on_message(filters.command(["blacklistchat", "blchat"]) & sudo_only)
async def bl_chat_command(_, message: types.Message):
    chat_id = message.chat.id
    if len(message.command) > 1:
        try:
            chat_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Provide valid numerical chat ID.")

    await db.blacklist_chat(chat_id)
    await message.reply_text(f"🚫 Chat <code>{chat_id}</code> is now blacklisted.")


@bot.on_message(filters.command(["whitelistchat", "unblchat"]) & sudo_only)
async def unbl_chat_command(_, message: types.Message):
    chat_id = message.chat.id
    if len(message.command) > 1:
        try:
            chat_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Provide valid numerical chat ID.")

    await db.whitelist_chat(chat_id)
    await message.reply_text(f"✅ Chat <code>{chat_id}</code> is now whitelisted.")


@bot.on_message(filters.command(["blacklistedchats"]) & sudo_only)
async def list_bl_chats(_, message: types.Message):
    chats = db.blacklisted_chats
    if not chats:
        return await message.reply_text("ℹ️ No blacklisted chats.")
    text = "🚫 <b>Blacklisted Chats:</b>\n\n"
    for cid in chats:
        text += f"• <code>{cid}</code>\n"
    await message.reply_text(text)
