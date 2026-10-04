from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import sudo_only


@bot.on_message(filters.command(["gban"]) & sudo_only)
async def gban_command(_, message: types.Message):
    target_user = None
    reason = "No reason provided"

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        if len(message.command) > 1:
            reason = " ".join(message.command[1:])
    elif len(message.command) > 1:
        try:
            target_user = await bot.get_users(message.command[1])
            if len(message.command) > 2:
                reason = " ".join(message.command[2:])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target_user:
        return await message.reply_text("Usage: <code>/gban @username [reason]</code>")

    if db.is_sudo(target_user.id):
        return await message.reply_text("⚠️ Cannot GBan a sudo user.")

    await db.gban_user(target_user.id, reason)
    await message.reply_text(
        f"🔨 <b>Globally Banned User:</b>\n"
        f"• <b>User:</b> {target_user.mention} (<code>{target_user.id}</code>)\n"
        f"• <b>Reason:</b> {reason}"
    )


@bot.on_message(filters.command(["ungban"]) & sudo_only)
async def ungban_command(_, message: types.Message):
    target_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await bot.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target_user:
        return await message.reply_text("Usage: <code>/ungban @username</code>")

    await db.ungban_user(target_user.id)
    await message.reply_text(f"🕊 <b>Un-GBanned:</b> {target_user.mention} (<code>{target_user.id}</code>)")
