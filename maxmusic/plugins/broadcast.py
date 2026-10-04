import asyncio
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import sudo_only


@bot.on_message(filters.command(["broadcast", "gcast"]) & sudo_only)
async def broadcast_command(_, message: types.Message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("Usage: Reply to a message or provide text: <code>/broadcast [text]</code>")

    status_msg = await message.reply_text("📢 <i>Broadcasting message across all served chats...</i>")
    success_count = 0
    fail_count = 0

    target_msg = message.reply_to_message
    content = " ".join(message.command[1:]) if not target_msg else ""

    chats_cursor = db._db.chats.find({})
    async for chat_doc in chats_cursor:
        cid = chat_doc.get("chat_id")
        if not cid:
            continue
        try:
            if target_msg:
                await target_msg.copy(cid)
            else:
                await bot.send_message(cid, content)
            success_count += 1
            await asyncio.sleep(0.1)
        except Exception:
            fail_count += 1

    await status_msg.edit_text(
        f"📢 <b>Broadcast Completed!</b>\n\n"
        f"✅ <b>Delivered:</b> {success_count} chats\n"
        f"❌ <b>Failed:</b> {fail_count} chats"
    )
