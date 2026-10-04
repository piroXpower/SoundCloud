from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import owner_only, sudo_only
from maxmusic.config import config


@bot.on_message(filters.command(["addsudo"]) & owner_only)
async def add_sudo_command(_, message: types.Message):
    target_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await bot.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target_user:
        return await message.reply_text("Usage: <code>/addsudo @username</code> or reply to user.")

    added = await db.add_sudo(target_user.id)
    if added:
        await message.reply_text(f"👑 <b>Added {target_user.mention} to Bot Sudoers!</b>")
    else:
        await message.reply_text(f"ℹ️ {target_user.mention} is already a sudo user.")


@bot.on_message(filters.command(["delsudo", "removesudo"]) & owner_only)
async def del_sudo_command(_, message: types.Message):
    target_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await bot.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")

    if not target_user:
        return await message.reply_text("Usage: <code>/delsudo @username</code>")

    if target_user.id == config.OWNER_ID:
        return await message.reply_text("⚠️ You cannot remove the bot owner from sudoers.")

    removed = await db.remove_sudo(target_user.id)
    if removed:
        await message.reply_text(f"❌ <b>Removed {target_user.mention} from Sudoers.</b>")
    else:
        await message.reply_text(f"ℹ️ {target_user.mention} is not in the sudoers list.")


@bot.on_message(filters.command(["sudolist", "sudoers"]) & sudo_only)
async def sudo_list_command(_, message: types.Message):
    sudoers = db.get_sudoers()
    text = "👑 <b>Bot Sudoers List:</b>\n\n"
    for idx, uid in enumerate(sudoers, start=1):
        role = " (Owner)" if uid == config.OWNER_ID else ""
        try:
            u = await bot.get_users(uid)
            text += f"{idx}. {u.mention} [<code>{uid}</code>]{role}\n"
        except Exception:
            text += f"{idx}. <code>{uid}</code>{role}\n"

    await message.reply_text(text)
