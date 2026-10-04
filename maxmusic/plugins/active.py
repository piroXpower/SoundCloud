from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.database import db
from maxmusic.helpers.filters import sudo_only


@bot.on_message(filters.command(["activevc", "activevoice"]) & sudo_only)
async def active_vc_command(_, message: types.Message):
    calls = db.active_calls
    if not calls:
        return await message.reply_text("ℹ️ No active voice chats currently running.")

    text = f"🔊 <b>Active Voice Chats ({len(calls)}):</b>\n\n"
    for idx, (chat_id, data) in enumerate(calls.items(), start=1):
        try:
            chat = await bot.get_chat(chat_id)
            title = chat.title or "Private Group"
        except Exception:
            title = "Unknown Chat"
        status = "⏸ Paused" if data.get("paused") else "▶️ Playing"
        v_tag = " [Video]" if data.get("video") else " [Audio]"
        text += f"{idx}. <b>{title}</b> (<code>{chat_id}</code>)\n   Status: {status}{v_tag}\n\n"

    await message.reply_text(text)


@bot.on_message(filters.command(["activevideo", "activev"]) & sudo_only)
async def active_video_command(_, message: types.Message):
    video_calls = {cid: d for cid, d in db.active_calls.items() if d.get("video")}
    if not video_calls:
        return await message.reply_text("ℹ️ No active video streams currently running.")

    text = f"📺 <b>Active Video Streams ({len(video_calls)}):</b>\n\n"
    for idx, (chat_id, data) in enumerate(video_calls.items(), start=1):
        try:
            chat = await bot.get_chat(chat_id)
            title = chat.title or "Private Group"
        except Exception:
            title = "Unknown Chat"
        text += f"{idx}. <b>{title}</b> (<code>{chat_id}</code>)\n"

    await message.reply_text(text)
