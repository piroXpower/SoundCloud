import math
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus

from config import SUDO_USERS
from core.call import call_manager
from utils.queue import queue_mgr
from utils.inline import player_keyboard, volume_keyboard, queue_keyboard
from utils.formatters import format_duration, clean_html

async def check_admin_or_requester(client: Client, query: CallbackQuery, chat_id: int) -> bool:
    user_id = query.from_user.id
    if user_id in SUDO_USERS:
        return True

    # Check if user is track requester
    curr = queue_mgr.get_current(chat_id)
    if curr and curr.get("requester_id") == user_id:
        return True

    # Check if admin
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return True
    except Exception:
        pass

    await query.answer("⚠️ You must be an admin or the track requester to use this control!", show_alert=True)
    return False

@Client.on_callback_query(filters.regex(r"^ctrl_pause_(-?\d+)$"))
async def cb_pause(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    curr = queue_mgr.get_current(chat_id)
    if not curr:
        return await query.answer("❌ Nothing is currently playing.", show_alert=True)

    await call_manager.pause(chat_id)
    await query.answer("⏸ Playback Paused")
    
    # Update keyboard
    markup = player_keyboard(
        chat_id=chat_id,
        is_paused=True,
        loop_mode=queue_mgr.get_loop(chat_id),
        sc_url=curr.get("url", ""),
    )
    try:
        await query.message.edit_reply_markup(reply_markup=markup)
    except Exception:
        pass

@Client.on_callback_query(filters.regex(r"^ctrl_resume_(-?\d+)$"))
async def cb_resume(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    curr = queue_mgr.get_current(chat_id)
    if not curr:
        return await query.answer("❌ Nothing is currently playing.", show_alert=True)

    await call_manager.resume(chat_id)
    await query.answer("▶️ Playback Resumed")

    markup = player_keyboard(
        chat_id=chat_id,
        is_paused=False,
        loop_mode=queue_mgr.get_loop(chat_id),
        sc_url=curr.get("url", ""),
    )
    try:
        await query.message.edit_reply_markup(reply_markup=markup)
    except Exception:
        pass

@Client.on_callback_query(filters.regex(r"^ctrl_skip_(-?\d+)$"))
async def cb_skip(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    await query.answer("⏭ Skipping track...")
    await call_manager._on_stream_end(chat_id)

@Client.on_callback_query(filters.regex(r"^ctrl_stop_(-?\d+)$"))
async def cb_stop(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    await call_manager.stop(chat_id)
    await query.answer("⏹ Stream stopped and queue cleared!")
    try:
        await query.message.edit_caption(
            caption="🛑 <b>Stream Ended</b> by an administrator.\nVoice chat connection closed.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}")]])
        )
    except Exception:
        try:
            await query.message.edit_text(
                "🛑 <b>Stream Ended</b> by an administrator.\nVoice chat connection closed.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}")]])
            )
        except Exception:
            pass

@Client.on_callback_query(filters.regex(r"^ctrl_loop_(-?\d+)$"))
async def cb_loop(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    new_mode = queue_mgr.toggle_loop(chat_id)
    curr = queue_mgr.get_current(chat_id)
    
    label = "Loop Disabled" if new_mode == "none" else f"Loop set to: {new_mode.capitalize()}"
    await query.answer(f"🔁 {label}")

    markup = player_keyboard(
        chat_id=chat_id,
        is_paused=queue_mgr.is_paused(chat_id),
        loop_mode=new_mode,
        sc_url=curr.get("url", "") if curr else "",
    )
    try:
        await query.message.edit_reply_markup(reply_markup=markup)
    except Exception:
        pass

@Client.on_callback_query(filters.regex(r"^ctrl_mute_(-?\d+)$"))
async def cb_mute(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    await call_manager.mute(chat_id)
    await query.answer("🔇 Assistant muted in voice chat.")

@Client.on_callback_query(filters.regex(r"^ctrl_unmute_(-?\d+)$"))
async def cb_unmute(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    await call_manager.unmute(chat_id)
    await query.answer("🔊 Assistant unmuted in voice chat.")

@Client.on_callback_query(filters.regex(r"^ctrl_volmenu_(-?\d+)$"))
async def cb_volmenu(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    vol = queue_mgr.get_volume(chat_id)
    await query.edit_message_reply_markup(reply_markup=volume_keyboard(chat_id, vol))

@Client.on_callback_query(filters.regex(r"^vol_(up|down)_(-?\d+)$"))
async def cb_vol_change(client: Client, query: CallbackQuery):
    direction = query.matches[0].group(1)
    chat_id = int(query.matches[0].group(2))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    vol = queue_mgr.get_volume(chat_id)
    vol = min(200, vol + 10) if direction == "up" else max(10, vol - 10)
    await call_manager.set_volume(chat_id, vol)
    await query.answer(f"Volume: {vol}%")
    await query.edit_message_reply_markup(reply_markup=volume_keyboard(chat_id, vol))

@Client.on_callback_query(filters.regex(r"^vol_set_(-?\d+)_(\d+)$"))
async def cb_vol_set(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    level = int(query.matches[0].group(2))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    await call_manager.set_volume(chat_id, level)
    await query.answer(f"Volume set to: {level}%")
    await query.edit_message_reply_markup(reply_markup=volume_keyboard(chat_id, level))

@Client.on_callback_query(filters.regex(r"^vol_info_(-?\d+)$"))
async def cb_vol_info(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    vol = queue_mgr.get_volume(chat_id)
    await query.answer(f"Current stream volume: {vol}%", show_alert=True)

@Client.on_callback_query(filters.regex(r"^ctrl_queue_(-?\d+)_(\d+)$"))
async def cb_queue_view(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    page = int(query.matches[0].group(2))

    curr = queue_mgr.get_current(chat_id)
    tracks = queue_mgr.get_queue(chat_id)

    if not curr and not tracks:
        return await query.answer("📜 SoundCloud Queue is currently empty!", show_alert=True)

    items_per_page = 5
    total_pages = max(1, math.ceil(len(tracks) / items_per_page))
    page = min(page, total_pages - 1)

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_tracks = tracks[start_idx:end_idx]

    text = "📜 <b>SoundCloud Up Next Queue:</b>\n\n"
    if curr:
        text += f"🎧 <b>Now Playing:</b>\n └ <code>{clean_html(curr['title'])}</code> ({format_duration(curr.get('duration_sec', 0))})\n\n"

    if page_tracks:
        text += "📋 <b>Upcoming in Queue:</b>\n"
        for i, tr in enumerate(page_tracks, start=start_idx + 1):
            text += f" <b>{i}.</b> <code>{clean_html(tr['title'])}</code> ({format_duration(tr.get('duration_sec', 0))})\n"
    else:
        text += "<i>No other tracks pending in queue.</i>\n"

    text += f"\n📄 <b>Page:</b> {page + 1}/{total_pages} | <b>Total Tracks:</b> {len(tracks)}"

    try:
        # Check if message has caption (photo) or text
        if query.message.photo:
            await query.message.edit_caption(
                caption=text,
                reply_markup=queue_keyboard(chat_id, page, total_pages)
            )
        else:
            await query.message.edit_text(
                text=text,
                reply_markup=queue_keyboard(chat_id, page, total_pages)
            )
    except Exception as e:
        await query.answer(f"Queue updated!")

@Client.on_callback_query(filters.regex(r"^ctrl_clearq_(-?\d+)$"))
async def cb_clear_queue(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    if not await check_admin_or_requester(client, query, chat_id):
        return

    tracks = queue_mgr.get_queue(chat_id)
    tracks.clear()
    await query.answer("🧹 Queue cleared successfully!")
    await cb_queue_view(client, query)

@Client.on_callback_query(filters.regex(r"^ctrl_back_(-?\d+)$"))
async def cb_back_to_player(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    curr = queue_mgr.get_current(chat_id)
    if not curr:
        return await query.answer("Player is not active.", show_alert=True)

    markup = player_keyboard(
        chat_id=chat_id,
        is_paused=queue_mgr.is_paused(chat_id),
        loop_mode=queue_mgr.get_loop(chat_id),
        sc_url=curr.get("url", ""),
    )

    caption = (
        f"☁️ <b>Now Streaming on SoundCloud:</b>\n\n"
        f"🎵 <b>Title:</b> <a href=\"{curr['url']}\">{clean_html(curr['title'])}</a>\n"
        f"👤 <b>Artist:</b> <code>{clean_html(curr['uploader'])}</code>\n"
        f"⏱ <b>Duration:</b> <code>{format_duration(curr.get('duration_sec', 0))}</code>\n"
        f"🎧 <b>Requested by:</b> {curr.get('requester_mention', 'Listener')}\n\n"
        f"<blockquote>⚡ <i>Crystal-clear 320kbps audio directly from SoundCloud</i></blockquote>"
    )

    try:
        if query.message.photo:
            await query.message.edit_caption(caption=caption, reply_markup=markup)
        else:
            await query.message.edit_text(text=caption, reply_markup=markup)
    except Exception:
        await query.edit_message_reply_markup(reply_markup=markup)

@Client.on_callback_query(filters.regex(r"^ctrl_close_(-?\d+)$"))
async def cb_close(client: Client, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception:
        await query.answer("Closed!")

@Client.on_callback_query(filters.regex("^noop$"))
async def cb_noop(client: Client, query: CallbackQuery):
    await query.answer()
