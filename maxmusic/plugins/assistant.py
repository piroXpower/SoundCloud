from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.userbot import userbot
from maxmusic.helpers.filters import sudo_only


@bot.on_message(filters.command(["assistant", "userbot", "assistants"]))
async def assistant_status_command(_, message: types.Message):
    text = f"🤖 <b>{len(userbot.clients)} Assistant Client(s) Online:</b>\n\n"
    for idx, client in enumerate(userbot.clients, start=1):
        me = getattr(client, "me", None)
        if me:
            text += (
                f"<b>Assistant {idx}:</b>\n"
                f"• <b>Name:</b> {me.first_name}\n"
                f"• <b>Username:</b> @{me.username or 'None'}\n"
                f"• <b>ID:</b> <code>{me.id}</code>\n\n"
            )
    await message.reply_text(text)


@bot.on_message(filters.command(["userbotjoin", "assistantjoin"]) & filters.group & sudo_only)
async def assistant_join_command(_, message: types.Message):
    chat = message.chat
    asst = userbot.get_assistant(chat.id)
    try:
        await asst.join_chat(chat.username or chat.id)
        await message.reply_text("✅ Assistant successfully joined this chat!")
    except Exception as e:
        await message.reply_text(f"❌ Assistant failed to join: {e}")
