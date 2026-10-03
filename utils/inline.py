from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPPORT_GROUP, UPDATES_CHANNEL

def start_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                "➕ Add Me To Your Group",
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton("📚 Commands", callback_data="help_main"),
            InlineKeyboardButton("📢 Updates", url=UPDATES_CHANNEL or "https://t.me"),
        ],
        [
            InlineKeyboardButton("💬 Support Chat", url=SUPPORT_GROUP or "https://t.me"),
            InlineKeyboardButton("☁️ SoundCloud", url="https://soundcloud.com"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

def player_keyboard(chat_id: int, is_paused: bool = False, loop_mode: str = "none", sc_url: str = "") -> InlineKeyboardMarkup:
    # Play / Pause state button
    pause_btn = (
        InlineKeyboardButton("▶️ Resume", callback_data=f"ctrl_resume_{chat_id}")
        if is_paused
        else InlineKeyboardButton("⏸ Pause", callback_data=f"ctrl_pause_{chat_id}")
    )

    # Loop indicator
    loop_icon = "🔁 Loop: Off"
    if loop_mode == "track":
        loop_icon = "🔂 Track Loop"
    elif loop_mode == "queue":
        loop_icon = "🔁 Queue Loop"

    buttons = [
        [
            pause_btn,
            InlineKeyboardButton("⏭ Skip", callback_data=f"ctrl_skip_{chat_id}"),
            InlineKeyboardButton("⏹ Stop", callback_data=f"ctrl_stop_{chat_id}"),
        ],
        [
            InlineKeyboardButton(loop_icon, callback_data=f"ctrl_loop_{chat_id}"),
            InlineKeyboardButton("📜 Queue", callback_data=f"ctrl_queue_{chat_id}_0"),
            InlineKeyboardButton("🎚 Vol", callback_data=f"ctrl_volmenu_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🔇 Mute", callback_data=f"ctrl_mute_{chat_id}"),
            InlineKeyboardButton("🔊 Unmute", callback_data=f"ctrl_unmute_{chat_id}"),
        ],
    ]
    
    if sc_url:
        buttons.append([
            InlineKeyboardButton("☁️ Open on SoundCloud", url=sc_url),
            InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}"),
        ])
    else:
        buttons.append([
            InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}")
        ])

    return InlineKeyboardMarkup(buttons)

def volume_keyboard(chat_id: int, current_vol: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🔉 -10%", callback_data=f"vol_down_{chat_id}"),
            InlineKeyboardButton(f"🔊 {current_vol}%", callback_data=f"vol_info_{chat_id}"),
            InlineKeyboardButton("🔊 +10%", callback_data=f"vol_up_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🔈 50%", callback_data=f"vol_set_{chat_id}_50"),
            InlineKeyboardButton("🔉 100%", callback_data=f"vol_set_{chat_id}_100"),
            InlineKeyboardButton("🔊 150%", callback_data=f"vol_set_{chat_id}_150"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Player", callback_data=f"ctrl_back_{chat_id}"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

def queue_keyboard(chat_id: int, page: int, total_pages: int) -> InlineKeyboardMarkup:
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"ctrl_queue_{chat_id}_{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"ctrl_queue_{chat_id}_{page+1}"))

    buttons = [
        nav_buttons,
        [
            InlineKeyboardButton("🧹 Clear Queue", callback_data=f"ctrl_clearq_{chat_id}"),
            InlineKeyboardButton("🔙 Back to Player", callback_data=f"ctrl_back_{chat_id}"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

def help_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🎵 Music Player", callback_data="help_play"),
            InlineKeyboardButton("🛡 Admin Controls", callback_data="help_admin"),
        ],
        [
            InlineKeyboardButton("📂 Playlist & History", callback_data="help_pl"),
            InlineKeyboardButton("🎤 Lyrics & TTS", callback_data="help_extra"),
        ],
        [
            InlineKeyboardButton("🎚 Voice Chat & Vol", callback_data="help_vc"),
            InlineKeyboardButton("☁️ SoundCloud Guide", callback_data="help_sc"),
        ],
        [
            InlineKeyboardButton("🔙 Home", callback_data="help_home"),
            InlineKeyboardButton("🗑 Close", callback_data="close_help"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

def back_to_help_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🔙 Back to Help", callback_data="help_main"),
            InlineKeyboardButton("🗑 Close", callback_data="close_help"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)
