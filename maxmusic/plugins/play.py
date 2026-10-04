import os
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.core.downloader import downloader, Track
from maxmusic.core.calls import calls
from maxmusic.core.userbot import userbot
from maxmusic.core.database import db
from maxmusic.helpers.queue import queue_mgr
from maxmusic.config import config


@bot.on_message(filters.command(["play", "vplay", "playforce", "vplayforce"]) & filters.group)
async def play_command(_, message: types.Message):
    chat_id = message.chat.id
    user = message.from_user

    if user and db.is_user_blacklisted(user.id):
        return await message.reply_text("❌ You are blacklisted from using this bot.")
    if db.is_chat_blacklisted(chat_id):
        return await message.reply_text("❌ This chat is blacklisted from using this bot.")
    if db.maintenance_mode and not db.is_sudo(user.id if user else 0):
        return await message.reply_text("🚧 The bot is currently under maintenance. Please try again later.")

    cmd = message.command[0].lower()
    is_video = "v" in cmd
    is_force = "force" in cmd

    # Check play mode in settings
    settings = await db.get_chat_settings(chat_id)
    if settings.get("play_mode") == "Admin Only":
        from maxmusic.helpers.filters import is_admin_or_auth
        if not await is_admin_or_auth(bot, chat_id, user.id):
            return await message.reply_text("🔒 Playback is restricted to Administrators in this chat.")

    status_msg = await message.reply_text("🔎 <i>Searching...</i>")

    # Ensure assistant is in chat
    try:
        await userbot.join_assistant(chat_id, message.chat.username)
    except Exception:
        pass

    requester = user.mention if user else "Anonymous"
    track: Track | None = None

    # Case 1: Replied to Telegram Audio/Video File
    reply = message.reply_to_message
    if reply and (reply.audio or reply.video or reply.document):
        media = reply.audio or reply.video or reply.document
        await status_msg.edit_text("📥 <i>Downloading media file from Telegram...</i>")
        file_path = await bot.download_media(media, file_name=f"downloads/{reply.id}_{media.file_name or 'stream'}")
        dur = getattr(media, "duration", 0)
        track = Track(
            title=getattr(media, "file_name", "Telegram Audio"),
            duration=f"{dur // 60}:{dur % 60:02d}",
            duration_sec=dur,
            url=message.link or "",
            video_id=str(reply.id),
            thumbnail=config.DEFAULT_THUMB,
            requester=requester,
            stream_type="video" if (reply.video or is_video) else "audio",
            file_path=file_path,
        )

    # Case 2: Query or Link provided
    elif len(message.command) > 1:
        query = " ".join(message.command[1:]).strip()

        # Playlist check
        if "playlist" in query:
            await status_msg.edit_text("📑 <i>Fetching playlist tracks...</i>")
            tracks = await downloader.playlist(query, config.PLAYLIST_LIMIT, requester, is_video)
            if not tracks:
                return await status_msg.edit_text("❌ Could not load playlist. Ensure it is public.")

            track = tracks[0]
            # Enqueue remainder
            for rem_track in tracks[1:]:
                queue_mgr.add(chat_id, rem_track)
        else:
            track = await downloader.search(query, requester, is_video)

    if not track:
        return await status_msg.edit_text(
            f"❌ <b>No results found.</b>\n"
            f"Usage: <code>/{cmd} [Song Name or Link]</code>"
        )

    if track.duration_sec > config.DURATION_LIMIT:
        return await status_msg.edit_text(
            f"⚠️ Song exceeds maximum duration of {config.DURATION_LIMIT // 3600} hours."
        )

    # Playback handling
    is_active = db.is_call_active(chat_id)

    if is_force or not is_active:
        await status_msg.edit_text("🔄 <i>Starting playback stream...</i>")
        success = await calls.play(chat_id, track, video=is_video)
        if success:
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Failed to stream media into voice chat. Please ensure voice chat is open.")
    else:
        pos = queue_mgr.add(chat_id, track)
        if pos == -1:
            return await status_msg.edit_text(f"⚠️ Queue is full! Limit is {config.QUEUE_LIMIT} tracks.")

        await status_msg.edit_text(
            f"📑 <b>Queued At #{pos}</b>\n\n"
            f"📌 <b>Title:</b> <a href=\"{track.url}\">{track.title}</a>\n"
            f"⏱ <b>Duration:</b> {track.duration}\n"
            f"👤 <b>Requested By:</b> {track.requester}"
        )
