from pyrogram import filters, types
from maxmusic.core.bot import bot


@bot.on_message(filters.command(["id", "info"]))
async def id_command(_, message: types.Message):
    chat = message.chat
    user = message.from_user
    reply = message.reply_to_message

    text = f"📌 <b>Chat ID:</b> <code>{chat.id}</code>\n"
    if chat.title:
        text += f"🏷 <b>Chat Title:</b> {chat.title}\n"

    if user:
        text += f"\n👤 <b>Your User ID:</b> <code>{user.id}</code>\n"
        if user.username:
            text += f"🔗 <b>Username:</b> @{user.username}\n"

    if reply and reply.from_user:
        text += (
            f"\n💬 <b>Replied Message ID:</b> <code>{reply.id}</code>\n"
            f"👤 <b>Replied User ID:</b> <code>{reply.from_user.id}</code>\n"
        )
        if reply.from_user.username:
            text += f"🔗 <b>Replied Username:</b> @{reply.from_user.username}\n"

    await message.reply_text(text)
