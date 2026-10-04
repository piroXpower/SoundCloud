from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import is_admin_or_auth


@bot.on_message(filters.command(["auth", "dj"]) & filters.group)
async def auth_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Only Admins can authorize DJ users.")

    target_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await bot.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target_user:
        return await message.reply_text("Usage: Reply to a user or pass their username/ID: <code>/auth @username</code>")

    added = await db.add_auth_user(chat_id, target_user.id)
    if added:
        await message.reply_text(f"✅ {target_user.mention} is now authorized to control music in this chat.")
    else:
        await message.reply_text(f"ℹ️ {target_user.mention} was already authorized.")


@bot.on_message(filters.command(["unauth", "undj"]) & filters.group)
async def unauth_command(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Only Admins can remove authorized DJs.")

    target_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await bot.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target_user:
        return await message.reply_text("Usage: <code>/unauth @username</code>")

    removed = await db.remove_auth_user(chat_id, target_user.id)
    if removed:
        await message.reply_text(f"❌ Removed DJ privileges for {target_user.mention}.")
    else:
        await message.reply_text(f"ℹ️ {target_user.mention} was not authorized.")


@bot.on_message(filters.command(["authusers", "djlist"]) & filters.group)
async def auth_list_command(_, message: types.Message):
    chat_id = message.chat.id
    auths = await db.get_auth_users(chat_id)

    if not auths:
        return await message.reply_text("ℹ️ No authorized DJ users in this chat yet.")

    text = "🎧 <b>Authorized DJ Users:</b>\n\n"
    for idx, uid in enumerate(auths, start=1):
        try:
            u = await bot.get_users(uid)
            text += f"{idx}. {u.mention} (<code>{uid}</code>)\n"
        except Exception:
            text += f"{idx}. <code>{uid}</code>\n"

    await message.reply_text(text)
