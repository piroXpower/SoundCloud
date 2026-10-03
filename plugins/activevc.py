from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import SUDO_USERS, COMMAND_PREFIXES
from utils.queue import queue_mgr
from utils.formatters import clean_html, format_duration
from core.call import call_manager

@Client.on_message(filters.command(["activevc", "activecalls"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def active_vc_cmd(client: Client, message: Message):
    active_chats = [cid for cid, track in queue_mgr._current.items() if track]

    if not active_chats:
        return await message.reply_text("🔇 No active voice chats are currently streaming.")

    text = f"🎙️ <b>Active Voice Chats Streaming ({len(active_chats)}):</b>\n\n"
    buttons = []

    for idx, cid in enumerate(active_chats, start=1):
        curr = queue_mgr.get_current(cid)
        title = curr.get("title", "Unknown")[:25]
        vol = queue_mgr.get_volume(cid)
        dur = format_duration(curr.get("duration_sec", 0))

        text += (
            f"<b>{idx}. Chat ID:</b> <code>{cid}</code>\n"
            f"   🎵 <b>Song:</b> <code>{clean_html(title)}</code>\n"
            f"   ⏱ <b>Duration:</b> <code>{dur}</code> | 🔊 <code>{vol}%</code>\n\n"
        )
        buttons.append([InlineKeyboardButton(f"🛑 Stop Call #{idx}", callback_data=f"killvc_{cid}")])

    buttons.append([InlineKeyboardButton("🗑 Close", callback_data="activevc_close")])

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^killvc_(-?\d+)$"))
async def cb_kill_active_vc(client: Client, query: CallbackQuery):
    if query.from_user.id not in SUDO_USERS:
        return await query.answer("Sudo users only!", show_alert=True)

    chat_id = int(query.matches[0].group(1))
    await call_manager.stop(chat_id)
    await query.answer(f"Terminated voice call for {chat_id}")
    await query.message.edit_text(f"🛑 <b>Remotely stopped streaming in chat:</b> <code>{chat_id}</code>")

@Client.on_callback_query(filters.regex("^activevc_close$"))
async def cb_close_activevc(client: Client, query: CallbackQuery):
    await query.message.delete()
