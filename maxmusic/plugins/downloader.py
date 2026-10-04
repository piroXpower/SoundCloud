import os
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.downloader import downloader, Track


@bot.on_message(filters.command(["song", "vsong", "download"]))
async def download_command(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Usage:</b>\n"
            "• <code>/song [Song Title]</code> - Download Audio\n"
            "• <code>/vsong [Video Title]</code> - Download Video"
        )

    cmd = message.command[0].lower()
    is_video = "v" in cmd
    query = " ".join(message.command[1:])

    status_msg = await message.reply_text("🔎 <i>Searching media...</i>")
    track = await downloader.search(query, requester=message.from_user.mention if message.from_user else "User", video=is_video)
    if not track:
        return await status_msg.edit_text("❌ No results found on YouTube.")

    await status_msg.edit_text("📥 <i>Downloading file to server...</i>")
    file_path = await downloader.download(track)
    if not file_path or not os.path.exists(file_path):
        return await status_msg.edit_text("❌ Download failed.")

    await status_msg.edit_text("📤 <i>Uploading to Telegram...</i>")
    caption = (
        f"🎵 <b>{track.title}</b>\n\n"
        f"⏱ <b>Duration:</b> {track.duration}\n"
        f"👤 <b>Requested By:</b> {track.requester}"
    )

    try:
        if is_video:
            await message.reply_video(file_path, caption=caption)
        else:
            await message.reply_audio(file_path, caption=caption, title=track.title, duration=track.duration_sec)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Failed to upload media: {e}")
