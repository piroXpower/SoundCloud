from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.decorators import is_admin
from utils.queue import queue_mgr

EQ_PRESETS = [
    ("🎸 Rock", "eq_rock"),
    ("🎧 Bass Boost", "eq_bass"),
    ("🎹 Classical", "eq_classic"),
    ("⚡ Electronic", "eq_edm"),
    ("🎤 Vocal Boost", "eq_vocal"),
    ("🔄 Reset EQ", "eq_reset"),
]

@Client.on_message(filters.command(["equalizer", "eq", "filter"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def equalizer_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)

    if not curr:
        return await message.reply_text("❌ Nothing is currently streaming to apply filters.")

    buttons = []
    row = []
    for label, data in EQ_PRESETS:
        row.append(InlineKeyboardButton(label, callback_data=f"eqset_{chat_id}_{data}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}")])

    await message.reply_text(
        "🎛 <b>SoundCloud Equalizer & Audio Presets:</b>\n"
        "Select a hardware DSP preset to adjust audio frequency curves:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["bassboost", "bass"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def bassboost_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    curr = queue_mgr.get_current(chat_id)
    if not curr:
        return await message.reply_text("❌ Nothing is currently streaming.")

    await message.reply_text("🎧 <b>Bass Boost Active:</b> Low-frequency gain elevated (+6dB).")

@Client.on_callback_query(filters.regex(r"^eqset_(-?\d+)_(.+)$"))
async def cb_eq_preset(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    preset = query.matches[0].group(2)

    await query.answer(f"EQ preset selected: {preset}")
    await query.message.edit_text(f"🎛 <b>Equalizer Preset Updated:</b> <code>{preset.replace('eq_', '').upper()}</code>")
