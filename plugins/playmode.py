from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.decorators import is_admin

# chat_id -> {"direct": bool, "show_artwork": bool}
CHAT_SETTINGS = {}

def get_chat_settings(chat_id: int) -> dict:
    return CHAT_SETTINGS.setdefault(chat_id, {"direct": False, "show_artwork": True})

@Client.on_message(filters.command(["playmode", "settings"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def play_mode_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    settings = get_chat_settings(chat_id)

    mode_label = "Direct Play (Preempt)" if settings["direct"] else "Smart Queue (Standard)"
    art_label = "Enabled (HD Cards)" if settings["show_artwork"] else "Disabled (Compact Text)"

    buttons = [
        [
            InlineKeyboardButton(f"🔄 Mode: {mode_label}", callback_data=f"pm_toggle_mode_{chat_id}"),
        ],
        [
            InlineKeyboardButton(f"🎨 Artwork: {art_label}", callback_data=f"pm_toggle_art_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}"),
        ]
    ]

    await message.reply_text(
        "⚙️ <b>SoundCloud Playback Settings:</b>\n\n"
        f"• <b>Playback Mode:</b> <code>{mode_label}</code>\n"
        f"• <b>Now Playing Visuals:</b> <code>{art_label}</code>\n\n"
        "Tap the buttons below to customize group behavior:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^pm_toggle_(mode|art)_(-?\d+)$"))
async def cb_toggle_settings(client: Client, query: CallbackQuery):
    action = query.matches[0].group(1)
    chat_id = int(query.matches[0].group(2))

    settings = get_chat_settings(chat_id)
    if action == "mode":
        settings["direct"] = not settings["direct"]
        await query.answer("Playback mode toggled!")
    elif action == "art":
        settings["show_artwork"] = not settings["show_artwork"]
        await query.answer("Artwork visuals toggled!")

    mode_label = "Direct Play (Preempt)" if settings["direct"] else "Smart Queue (Standard)"
    art_label = "Enabled (HD Cards)" if settings["show_artwork"] else "Disabled (Compact Text)"

    buttons = [
        [
            InlineKeyboardButton(f"🔄 Mode: {mode_label}", callback_data=f"pm_toggle_mode_{chat_id}"),
        ],
        [
            InlineKeyboardButton(f"🎨 Artwork: {art_label}", callback_data=f"pm_toggle_art_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}"),
        ]
    ]

    await query.message.edit_text(
        "⚙️ <b>SoundCloud Playback Settings:</b>\n\n"
        f"• <b>Playback Mode:</b> <code>{mode_label}</code>\n"
        f"• <b>Now Playing Visuals:</b> <code>{art_label}</code>\n\n"
        "Tap the buttons below to customize group behavior:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
