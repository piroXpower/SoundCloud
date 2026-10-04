from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import sudo_only


@bot.on_message(filters.command(["maintenance"]) & sudo_only)
async def maintenance_command(_, message: types.Message):
    if len(message.command) < 2:
        status = "Enabled" if db.maintenance_mode else "Disabled"
        return await message.reply_text(
            f"🚧 <b>Maintenance Mode:</b> {status}\n\n"
            f"Usage:\n"
            f"• <code>/maintenance enable</code>\n"
            f"• <code>/maintenance disable</code>"
        )

    arg = message.command[1].lower()
    if arg in ("enable", "on", "true"):
        await db.set_maintenance(True)
        await message.reply_text("🚧 <b>Maintenance mode enabled.</b> Non-sudo users cannot use playback.")
    elif arg in ("disable", "off", "false"):
        await db.set_maintenance(False)
        await message.reply_text("✅ <b>Maintenance mode disabled.</b> Bot is fully open to all users.")
    else:
        await message.reply_text("Usage: <code>/maintenance [enable|disable]</code>")
