from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.filters import sudo_only
from maxmusic.config import config


@bot.on_message(filters.command(["logger", "loggroup"]) & sudo_only)
async def logger_command(_, message: types.Message):
    await message.reply_text(
        f"📝 <b>Bot Logger Information:</b>\n\n"
        f"• <b>Logger Group ID:</b> <code>{config.LOGGER_ID}</code>\n"
        f"• <b>Bot Owner ID:</b> <code>{config.OWNER_ID}</code>\n\n"
        f"All startup, errors, and system activity are automatically reported to the logger group."
    )
