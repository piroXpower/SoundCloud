from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.queue import queue_mgr
from core.call import call_manager
from utils.formatters import clean_html

# chat_id -> {"voters": set(user_ids), "threshold": 3, "track_title": str}
VOTE_DATA = {}

@Client.on_message(filters.command(["voteskip", "skipvote"], prefixes=COMMAND_PREFIXES) & filters.group)
async def vote_skip_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)

    if not curr:
        return await message.reply_text("❌ Nothing is currently streaming to vote skip.")

    user_id = message.from_user.id
    data = VOTE_DATA.setdefault(chat_id, {
        "voters": set(),
        "threshold": 3,
        "track_url": curr.get("url"),
    })

    # Reset if new track
    if data.get("track_url") != curr.get("url"):
        data["voters"] = set()
        data["track_url"] = curr.get("url")

    data["voters"].add(user_id)
    votes = len(data["voters"])
    needed = data["threshold"]

    if votes >= needed:
        data["voters"] = set()
        await message.reply_text("🗳 <b>Vote Skip Passed!</b> (3/3 votes). Skipping to next track...")
        return await call_manager._on_stream_end(chat_id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🗳 Vote Skip ({votes}/{needed})", callback_data=f"voteskip_{chat_id}"),
            InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}"),
        ]
    ])

    await message.reply_text(
        f"🗳 <b>Democratic Skip Vote Started!</b>\n\n"
        f"🎵 <b>Track:</b> <code>{clean_html(curr['title'])}</code>\n"
        f"📊 <b>Votes:</b> <code>{votes}/{needed}</code> members voted to skip.\n"
        f"👉 Tap the button below to add your vote!",
        reply_markup=keyboard,
    )

@Client.on_callback_query(filters.regex(r"^voteskip_(-?\d+)$"))
async def cb_vote_skip(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    curr = queue_mgr.get_current(chat_id)

    if not curr:
        return await query.answer("Nothing is currently streaming.", show_alert=True)

    data = VOTE_DATA.setdefault(chat_id, {
        "voters": set(),
        "threshold": 3,
        "track_url": curr.get("url"),
    })

    # Reset if track changed
    if data.get("track_url") != curr.get("url"):
        data["voters"] = set()
        data["track_url"] = curr.get("url")

    user_id = query.from_user.id
    if user_id in data["voters"]:
        return await query.answer("⚠️ You have already voted to skip this track!", show_alert=True)

    data["voters"].add(user_id)
    votes = len(data["voters"])
    needed = data["threshold"]

    await query.answer(f"Voted! ({votes}/{needed})")

    if votes >= needed:
        data["voters"] = set()
        await query.message.edit_text("🗳 <b>Vote Skip Threshold Reached!</b>\n⏭ Skipping to next track...")
        return await call_manager._on_stream_end(chat_id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🗳 Vote Skip ({votes}/{needed})", callback_data=f"voteskip_{chat_id}"),
            InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}"),
        ]
    ])

    await query.message.edit_text(
        f"🗳 <b>Democratic Skip Vote in Progress:</b>\n\n"
        f"🎵 <b>Track:</b> <code>{clean_html(curr['title'])}</code>\n"
        f"📊 <b>Votes:</b> <code>{votes}/{needed}</code> members voted to skip.\n"
        f"👉 Tap the button below to add your vote!",
        reply_markup=keyboard,
    )
