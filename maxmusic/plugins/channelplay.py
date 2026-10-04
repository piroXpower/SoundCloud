from pyrogram import filters, types
from pyrogram.enums import ChatMemberStatus
from maxmusic.core.bot import bot
from maxmusic.core.downloader import downloader, Track
from maxmusic.core.calls import calls
from maxmusic.core.userbot import userbot
from maxmusic.core.database import db
from maxmusic.helpers.queue import queue_mgr
from maxmusic.helpers.buttons import channel_play_markup
from maxmusic.helpers.filters import is_admin_or_auth
from maxmusic.config import config


@bot.on_message(filters.command(["channelplay", "cplaymode"]) & filters.group)
async def channel_play_cmd(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Only Group Admins can configure Channel Play.")

    if len(message.command) == 1:
        linked = db.get_channel(chat_id)
        return await message.reply_text(
            f"📡 <b>Channel Play Management</b>\n\n"
            f"🔗 <b>Linked Channel:</b> <code>{linked or 'None'}</code>\n\n"
            f"To link a channel:\n"
            f"<code>/channelplay [Channel ID or @username]</code>\n\n"
            f"To unlink:\n"
            f"<code>/channelplay disable</code>",
            reply_markup=channel_play_markup(chat_id, linked),
        )

    arg = message.command[1].strip()

    if arg.lower() in ("disable", "unlink", "off"):
        await db.remove_channel(chat_id)
        return await message.reply_text("✅ Successfully unlinked channel from this group.")

    # Try resolving the channel
    try:
        channel_chat = await bot.get_chat(arg)
        channel_id = channel_chat.id
    except Exception as e:
        return await message.reply_text(f"❌ Failed to find channel: {e}\nMake sure the bot is added as admin to that channel.")

    # Verify user is channel admin
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        if member.status not in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
            return await message.reply_text("❌ You must be an Administrator in that channel to link it.")
    except Exception:
        return await message.reply_text("❌ Could not verify your permissions in that channel.")

    # Ensure assistant joins channel
    try:
        asst = userbot.get_assistant(channel_id)
        await asst.join_chat(channel_chat.username or channel_id)
    except Exception:
        pass

    await db.set_channel(chat_id, channel_id)
    await message.reply_text(
        f"✅ <b>Channel Linked Successfully!</b>\n\n"
        f"📢 <b>Channel:</b> {channel_chat.title} (<code>{channel_id}</code>)\n"
        f"Now you can use <code>/cplay</code> and <code>/cvplay</code> to stream music in your channel VC!"
    )


@bot.on_message(filters.command(["cplay", "cvplay", "cplayforce", "cvplayforce"]) & filters.group)
async def cplay_command(_, message: types.Message):
    chat_id = message.chat.id
    channel_id = db.get_channel(chat_id)

    if not channel_id:
        return await message.reply_text(
            "⚠️ No channel is linked to this group!\n"
            "Use <code>/channelplay [channel_id]</code> to link one first."
        )

    user = message.from_user
    if user and db.is_user_blacklisted(user.id):
        return await message.reply_text("❌ You are blacklisted.")

    cmd = message.command[0].lower()
    is_video = "v" in cmd
    is_force = "force" in cmd

    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text(f"Usage: <code>/{cmd} [Song Name / URL]</code>")

    status_msg = await message.reply_text(f"🔎 <i>Searching for channel stream...</i>")

    query = " ".join(message.command[1:])
    requester = f"{user.mention} (via {message.chat.title})" if user else "Channel DJ"

    track = await downloader.search(query, requester, is_video)
    if not track:
        return await status_msg.edit_text("❌ Song not found.")

    is_active = db.is_call_active(channel_id)

    if is_force or not is_active:
        await status_msg.edit_text("🔄 <i>Starting channel stream...</i>")
        success = await calls.play(channel_id, track, video=is_video)
        if success:
            await status_msg.edit_text(
                f"📡 <b>Streaming In Channel VC:</b>\n"
                f"📌 <b>Title:</b> <a href=\"{track.url}\">{track.title}</a>\n"
                f"⏱ <b>Duration:</b> {track.duration}"
            )
        else:
            await status_msg.edit_text("❌ Failed to stream into channel voice chat. Ensure voice chat is active!")
    else:
        pos = queue_mgr.add(channel_id, track)
        await status_msg.edit_text(
            f"📡 <b>Queued For Channel VC (Position #{pos})</b>\n\n"
            f"📌 <b>Title:</b> <a href=\"{track.url}\">{track.title}</a>\n"
            f"⏱ <b>Duration:</b> {track.duration}"
        )


@bot.on_message(filters.command(["cstop", "cend", "cskip", "cpause", "cresume"]) & filters.group)
async def channel_controls(_, message: types.Message):
    chat_id = message.chat.id
    channel_id = db.get_channel(chat_id)
    if not channel_id:
        return await message.reply_text("⚠️ No linked channel.")

    user_id = message.from_user.id if message.from_user else 0
    if not await is_admin_or_auth(bot, chat_id, user_id):
        return await message.reply_text("🔒 Admin only.")

    cmd = message.command[0].lower()
    if cmd in ("cstop", "cend"):
        await calls.stop(channel_id)
        await message.reply_text("⏹ Channel stream stopped.")
    elif cmd == "cskip":
        await calls.play_next(channel_id)
        await message.reply_text("⏭ Skipped channel track.")
    elif cmd == "cpause":
        await calls.pause(channel_id)
        await message.reply_text("⏸ Channel stream paused.")
    elif cmd == "cresume":
        await calls.resume(channel_id)
        await message.reply_text("▶️ Channel stream resumed.")
