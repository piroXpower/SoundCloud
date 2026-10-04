from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.buttons import help_menu_markup
from maxmusic.config import config


@bot.on_message(filters.command(["help"]))
async def help_command(_, message: types.Message):
    text = (
        f"📖 <b>{config.BOT_NAME} Help & Documentation Center</b>\n\n"
        f"Select a category below to view detailed command instructions and usage examples:"
    )
    await message.reply_text(text, reply_markup=help_menu_markup())
