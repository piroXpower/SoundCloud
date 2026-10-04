from pyrogram import types
from maxmusic.core.bot import bot
from maxmusic.core.calls import calls
from maxmusic.core.database import db
from maxmusic.helpers.queue import queue_mgr
from maxmusic.helpers.buttons import (
    player_markup,
    queue_markup,
    volume_markup,
    speed_markup,
    settings_markup,
    help_menu_markup,
    help_back_markup,
)
from maxmusic.helpers.filters import is_admin_or_auth
from maxmusic.plugins.queue import get_queue_page_text
from maxmusic.config import config


@bot.on_callback_query()
async def callback_dispatcher(_, query: types.CallbackQuery):
    data = query.data
    user = query.from_user
    chat = query.message.chat if query.message else None

    if data == "cb_noop":
        return await query.answer()

    if data == "cb_close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return await query.answer("Closed")

    # --- Help Menu Callbacks ---
    if data == "help_main":
        text = (
            f"📖 <b>{config.BOT_NAME} Help & Documentation Center</b>\n\n"
            f"Select a category below to view detailed command instructions and usage examples:"
        )
        return await query.edit_message_text(text, reply_markup=help_menu_markup())

    if data == "help_play":
        text = (
            "🎵 <b>Playback Commands:</b>\n\n"
            "• <code>/play [Song/Link]</code> - Stream audio in group VC\n"
            "• <code>/vplay [Video/Link]</code> - Stream 720p HD video in VC\n"
            "• <code>/playforce [Song]</code> - Force play immediately\n"
            "• <code>/vplayforce [Video]</code> - Force play video\n"
            "• Reply to any audio/video document with <code>/play</code> to stream it directly!"
        )
        return await query.edit_message_text(text, reply_markup=help_back_markup())

    if data == "help_controls":
        text = (
            "🎛 <b>Player Control Commands:</b>\n\n"
            "• <code>/pause</code> - Pause the current stream\n"
            "• <code>/resume</code> - Resume paused playback\n"
            "• <code>/skip</code> or <code>/next</code> - Skip to next track\n"
            "• <code>/stop</code> or <code>/end</code> - Stop playback and clear queue\n"
            "• <code>/seek [seconds]</code> - Seek forward\n"
            "• <code>/seekback [seconds]</code> - Seek backward\n"
            "• <code>/loop [0|1|2]</code> - Repeat current track or queue\n"
            "• <code>/shuffle</code> - Randomize queued songs\n"
            "• <code>/queue</code> - Interactive paginated queue\n"
            "• <code>/volume [1-200]</code> - Adjust stream volume\n"
            "• <code>/speed</code> - Adjust playback speed (0.5x - 2.0x)\n"
            "• <code>/mute</code> & <code>/unmute</code> - Assistant VC mute controls"
        )
        return await query.edit_message_text(text, reply_markup=help_back_markup())

    if data == "help_admin":
        text = (
            "👑 <b>Admin & DJ Commands:</b>\n\n"
            "• <code>/auth @username</code> - Authorize user to control player\n"
            "• <code>/unauth @username</code> - Revoke DJ privileges\n"
            "• <code>/authusers</code> - List all authorized DJs\n"
            "• <code>/settings</code> - Configure chat playback permissions\n"
            "• <code>/cleanmode [on|off]</code> - Auto-delete command messages\n"
            "• <code>/reload</code> - Refresh group admin cache\n"
            "• <code>/thumb</code> - Set custom group playback card thumbnail"
        )
        return await query.edit_message_text(text, reply_markup=help_back_markup())

    if data == "help_channel":
        text = (
            "📡 <b>Channel Play Commands:</b>\n\n"
            "• <code>/channelplay [Channel_ID]</code> - Link group to a channel\n"
            "• <code>/cplay [Song]</code> - Stream audio in linked channel VC\n"
            "• <code>/cvplay [Video]</code> - Stream video in linked channel VC\n"
            "• <code>/cstop</code> - Stop channel voice chat stream\n"
            "• <code>/cskip</code> - Skip song in channel voice chat\n"
            "• <code>/cpause</code> & <code>/cresume</code> - Pause/Resume channel stream\n"
            "• <code>/channelplay disable</code> - Unlink channel from group"
        )
        return await query.edit_message_text(text, reply_markup=help_back_markup())

    if data == "help_sudo":
        text = (
            "⚡ <b>Sudoers & Maintenance Commands:</b>\n\n"
            "• <code>/activevc</code> & <code>/activevideo</code> - List active streams\n"
            "• <code>/broadcast [text]</code> - Broadcast to all groups\n"
            "• <code>/stats</code> - Live system CPU, RAM, disk & bot stats\n"
            "• <code>/speedtest</code> - Server network bandwidth speedtest\n"
            "• <code>/blacklistchat [chat_id]</code> - Block chat from bot\n"
            "• <code>/blacklistuser [user_id]</code> - Block user from bot\n"
            "• <code>/gban @username</code> - Global ban across all groups\n"
            "• <code>/maintenance [enable|disable]</code> - Toggle maintenance mode\n"
            "• <code>/restart</code> - Restart bot instance\n"
            "• <code>/update</code> - Pull updates from Git"
        )
        return await query.edit_message_text(text, reply_markup=help_back_markup())

    if data == "help_extra":
        text = (
            "⚙️ <b>Extra Utilities:</b>\n\n"
            "• <code>/song [Title]</code> - Download MP3 audio to Telegram\n"
            "• <code>/vsong [Title]</code> - Download MP4 video to Telegram\n"
            "• <code>/lyrics [Title]</code> - Search song lyrics\n"
            "• <code>/ping</code> - Check bot latency and uptime\n"
            "• <code>/id</code> - Inspect chat and user IDs\n"
            "• <code>/lang</code> - Change language preferences\n"
            "• <code>/assistant</code> - View connected assistant accounts"
        )
        return await query.edit_message_text(text, reply_markup=help_back_markup())

    # --- Interactive Playback Control Callbacks ---
    parts = data.split("_")
    action = parts[1] if len(parts) > 1 else ""

    # Check chat admin permissions for player actions
    if len(parts) >= 3 and parts[2].lstrip("-").isdigit():
        target_chat_id = int(parts[2])
    else:
        target_chat_id = chat.id if chat else 0

    if action in ("pause", "resume", "skip", "stop", "loop", "shuffle", "seekback", "speed", "volume", "autoplay"):
        if not await is_admin_or_auth(bot, target_chat_id, user.id):
            return await query.answer("🔒 Only Admins or Authorized DJs can use player controls.", show_alert=True)

    if action == "pause":
        await calls.pause(target_chat_id)
        await query.answer("⏸ Paused")
        return await query.edit_message_reply_markup(reply_markup=player_markup(target_chat_id, is_paused=True))

    if action == "resume":
        await calls.resume(target_chat_id)
        await query.answer("▶️ Resumed")
        return await query.edit_message_reply_markup(reply_markup=player_markup(target_chat_id, is_paused=False))

    if action == "skip":
        await query.answer("⏭ Skipped to next track")
        return await calls.play_next(target_chat_id)

    if action == "stop":
        await calls.stop(target_chat_id)
        await query.answer("⏹ Playback stopped")
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    if action == "seekback":
        await calls.seek(target_chat_id, 0)
        return await query.answer("⏪ Rewound to beginning")

    if action == "loop":
        curr = queue_mgr.get_loop(target_chat_id)
        new_mode = (curr + 1) % 3
        queue_mgr.set_loop(target_chat_id, new_mode)
        mode_str = "Disabled" if new_mode == 0 else ("Single Track" if new_mode == 1 else "Entire Queue")
        return await query.answer(f"🔁 Loop Mode: {mode_str}", show_alert=True)

    if action == "shuffle":
        if queue_mgr.shuffle(target_chat_id):
            return await query.answer("🔀 Queue Shuffled!")
        return await query.answer("⚠️ Not enough tracks to shuffle.", show_alert=True)

    if action == "autoplay":
        curr_auto = queue_mgr.is_autoplay(target_chat_id)
        queue_mgr.set_autoplay(target_chat_id, not curr_auto)
        return await query.answer(f"✨ Autoplay: {'Enabled' if not curr_auto else 'Disabled'}")

    if action == "volume":
        return await query.edit_message_reply_markup(reply_markup=volume_markup(target_chat_id))

    if action == "setvol" and len(parts) >= 4:
        vol = int(parts[3])
        await calls.set_volume(target_chat_id, vol)
        await query.answer(f"🔊 Volume: {vol}%")
        return await query.edit_message_reply_markup(reply_markup=player_markup(target_chat_id))

    if action == "speed":
        return await query.edit_message_reply_markup(reply_markup=speed_markup(target_chat_id))

    if action == "setspeed" and len(parts) >= 4:
        speed = float(parts[3])
        # Setting speed
        await query.answer(f"⚡ Playback Speed: {speed}x")
        return await query.edit_message_reply_markup(reply_markup=player_markup(target_chat_id))

    if action == "backplayer":
        return await query.edit_message_reply_markup(reply_markup=player_markup(target_chat_id))

    # --- Queue Pagination Callback ---
    if action == "queue" and len(parts) >= 4:
        page = int(parts[3])
        text, total_pages = get_queue_page_text(target_chat_id, page=page)
        await query.answer()
        return await query.edit_message_text(
            text,
            reply_markup=queue_markup(target_chat_id, page=page, total_pages=total_pages),
            disable_web_page_preview=True
        )

    # --- Settings Callbacks ---
    if action == "toggle" and len(parts) >= 4:
        setting_key = parts[2]
        settings = await db.get_chat_settings(target_chat_id)

        if setting_key == "playmode":
            curr = settings.get("play_mode", "Everyone")
            new_val = "Admin Only" if curr == "Everyone" else "Everyone"
            await db.update_chat_setting(target_chat_id, "play_mode", new_val)
        elif setting_key == "clean":
            curr = settings.get("clean_mode", True)
            await db.update_chat_setting(target_chat_id, "clean_mode", not curr)
        elif setting_key == "quality":
            curr = settings.get("quality", "High")
            new_val = "Medium" if curr == "High" else "High"
            await db.update_chat_setting(target_chat_id, "quality", new_val)

        settings = await db.get_chat_settings(target_chat_id)
        await query.answer("Updated setting")
        return await query.edit_message_reply_markup(reply_markup=settings_markup(target_chat_id, settings))

    # --- Language Callbacks ---
    if action == "setlang" and len(parts) >= 4:
        lang_code = parts[3]
        await db.set_lang(target_chat_id, lang_code)
        return await query.answer(f"✅ Language updated to {lang_code.upper()}!", show_alert=True)

    # --- Channel Unlink Callback ---
    if action == "unlink" and parts[2] == "channel":
        await db.remove_channel(target_chat_id)
        await query.answer("Channel unlinked!")
        try:
            await query.message.delete()
        except Exception:
            pass
