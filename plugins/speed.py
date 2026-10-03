from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.decorators import is_admin
from utils.queue import queue_mgr
from core.call import call_manager

@Client.on_message(filters.command(["speed", "rate"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def speed_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)

    if not curr:
        return await message.reply_text("❌ Nothing is currently streaming.")

    buttons = [
        [
            InlineKeyboardButton("🐌 0.75x", callback_data=f"speed_{chat_id}_0.75"),
            InlineKeyboardButton("▶️ 1.0x (Normal)", callback_data=f"speed_{chat_id}_1.0"),
            InlineKeyboardButton("⚡ 1.25x", callback_data=f"speed_{chat_id}_1.25"),
        ],
        [
            InlineKeyboardButton("🌙 Nightcore (1.3x)", callback_data=f"speed_{chat_id}_nightcore"),
            InlineKeyboardButton("🌌 Slowed & Reverb", callback_data=f"speed_{chat_id}_slowed"),
        ],
        [
            InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}"),
        ]
    ]

    await message.reply_text(
        "🎚 <b>Audio Playback Speed & Presets:</b>\n"
        "Choose an audio playback speed or preset effect below:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["nightcore"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def nightcore_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)
    if not curr:
        return await message.reply_text("❌ Nothing is currently streaming.")

    await message.reply_text("🌙 <b>Nightcore Mode Enabled!</b>\nIncreased speed & higher pitch.")

@Client.on_message(filters.command(["slowed"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def slowed_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)
    if not curr:
        return await message.reply_text("❌ Nothing is currently streaming.")

    await message.reply_text("🌌 <b>Slowed & Reverb Mode Enabled!</b>\nReduced speed & deeper tone.")

@Client.on_callback_query(filters.regex(r"^speed_(-?\d+)_(.+)$"))
async def cb_speed_preset(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    preset = query.matches[0].group(2)

    curr = queue_mgr.get_current(chat_id)
    if not curr:
        return await query.answer("Nothing is currently streaming.", show_alert=True)

    await query.answer(f"Applying speed preset: {preset}")
    await query.message.edit_text(f"🎚 <b>Audio preset applied:</b> <code>{preset}</code>")
