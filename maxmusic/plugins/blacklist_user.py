from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import sudo_only


@bot.on_message(filters.command(["blacklistuser", "bluser"]) & sudo_only)
async def bl_user_command(_, message: types.Message):
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await bot.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target:
        return await message.reply_text("Usage: <code>/blacklistuser @username</code> or reply to user.")

    if db.is_sudo(target.id):
        return await message.reply_text("⚠️ Cannot blacklist a sudo user.")

    await db.blacklist_user(target.id)
    await message.reply_text(f"🚫 {target.mention} is now blacklisted from all bot operations.")


@bot.on_message(filters.command(["whitelistuser", "unbluser"]) & sudo_only)
async def unbl_user_command(_, message: types.Message):
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await bot.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target:
        return await message.reply_text("Usage: <code>/whitelistuser @username</code>")

    await db.whitelist_user(target.id)
    await message.reply_text(f"✅ {target.mention} has been whitelisted.")
