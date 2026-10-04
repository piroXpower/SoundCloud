from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from maxmusic.config import config


def player_markup(chat_id: int, is_paused: bool = False) -> InlineKeyboardMarkup:
    play_pause = "▶️ Resume" if is_paused else "⏸ Pause"
    play_callback = f"cb_resume_{chat_id}" if is_paused else f"cb_pause_{chat_id}"

    buttons = [
        [
            InlineKeyboardButton("⏪ 10s", callback_data=f"cb_seekback_{chat_id}"),
            InlineKeyboardButton(play_pause, callback_data=play_callback),
            InlineKeyboardButton("⏭ Skip", callback_data=f"cb_skip_{chat_id}"),
            InlineKeyboardButton("⏹ Stop", callback_data=f"cb_stop_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🔁 Loop", callback_data=f"cb_loop_{chat_id}"),
            InlineKeyboardButton("🔀 Shuffle", callback_data=f"cb_shuffle_{chat_id}"),
            InlineKeyboardButton("📜 Queue", callback_data=f"cb_queue_{chat_id}_1"),
            InlineKeyboardButton("🔊 Vol", callback_data=f"cb_volume_{chat_id}"),
        ],
        [
            InlineKeyboardButton("⚡ Speed", callback_data=f"cb_speed_{chat_id}"),
            InlineKeyboardButton("✨ Autoplay", callback_data=f"cb_autoplay_{chat_id}"),
        ],
        [
            InlineKeyboardButton("💬 Support", url=config.SUPPORT_CHAT),
            InlineKeyboardButton("📢 Channel", url=config.SUPPORT_CHANNEL),
            InlineKeyboardButton("🗑 Close", callback_data="cb_close"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def queue_markup(chat_id: int, page: int, total_pages: int) -> InlineKeyboardMarkup:
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"cb_queue_{chat_id}_{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="cb_noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"cb_queue_{chat_id}_{page + 1}"))

    return InlineKeyboardMarkup([
        nav,
        [
            InlineKeyboardButton("🔄 Refresh", callback_data=f"cb_queue_{chat_id}_{page}"),
            InlineKeyboardButton("🗑 Close", callback_data="cb_close"),
        ]
    ])


def speed_markup(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("0.5x", callback_data=f"cb_setspeed_{chat_id}_0.5"),
            InlineKeyboardButton("0.75x", callback_data=f"cb_setspeed_{chat_id}_0.75"),
            InlineKeyboardButton("1.0x (Normal)", callback_data=f"cb_setspeed_{chat_id}_1.0"),
        ],
        [
            InlineKeyboardButton("1.25x", callback_data=f"cb_setspeed_{chat_id}_1.25"),
            InlineKeyboardButton("1.5x", callback_data=f"cb_setspeed_{chat_id}_1.5"),
            InlineKeyboardButton("2.0x", callback_data=f"cb_setspeed_{chat_id}_2.0"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data=f"cb_backplayer_{chat_id}"),
            InlineKeyboardButton("🗑 Close", callback_data="cb_close"),
        ]
    ])


def volume_markup(chat_id: int, current_vol: int = 100) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("25%", callback_data=f"cb_setvol_{chat_id}_25"),
            InlineKeyboardButton("50%", callback_data=f"cb_setvol_{chat_id}_50"),
            InlineKeyboardButton("75%", callback_data=f"cb_setvol_{chat_id}_75"),
            InlineKeyboardButton("100%", callback_data=f"cb_setvol_{chat_id}_100"),
            InlineKeyboardButton("150%", callback_data=f"cb_setvol_{chat_id}_150"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data=f"cb_backplayer_{chat_id}"),
            InlineKeyboardButton("🗑 Close", callback_data="cb_close"),
        ]
    ])


def settings_markup(chat_id: int, settings: dict) -> InlineKeyboardMarkup:
    play_mode = settings.get("play_mode", "Everyone")
    clean_mode = "ON" if settings.get("clean_mode", True) else "OFF"
    quality = settings.get("quality", "High").capitalize()

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 Play Mode", callback_data="cb_noop"),
            InlineKeyboardButton(f"{play_mode}", callback_data=f"cb_toggle_playmode_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🧹 Clean Mode", callback_data="cb_noop"),
            InlineKeyboardButton(f"{clean_mode}", callback_data=f"cb_toggle_clean_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🎧 Stream Quality", callback_data="cb_noop"),
            InlineKeyboardButton(f"{quality}", callback_data=f"cb_toggle_quality_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🗑 Close", callback_data="cb_close"),
        ]
    ])


def channel_play_markup(chat_id: int, linked_channel: int | None = None) -> InlineKeyboardMarkup:
    status_text = f"Linked: {linked_channel}" if linked_channel else "Not Linked"
    buttons = [
        [
            InlineKeyboardButton("Status", callback_data="cb_noop"),
            InlineKeyboardButton(status_text, callback_data="cb_noop"),
        ]
    ]
    if linked_channel:
        buttons.append([
            InlineKeyboardButton("❌ Unlink Channel", callback_data=f"cb_unlink_channel_{chat_id}")
        ])
    buttons.append([
        InlineKeyboardButton("🗑 Close", callback_data="cb_close")
    ])
    return InlineKeyboardMarkup(buttons)


def help_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Playback", callback_data="help_play"),
            InlineKeyboardButton("🎛 Controls", callback_data="help_controls"),
        ],
        [
            InlineKeyboardButton("👑 Admin & DJ", callback_data="help_admin"),
            InlineKeyboardButton("📡 Channel Play", callback_data="help_channel"),
        ],
        [
            InlineKeyboardButton("⚡ Sudo & Tools", callback_data="help_sudo"),
            InlineKeyboardButton("⚙️ Settings & Info", callback_data="help_extra"),
        ],
        [
            InlineKeyboardButton("💬 Support Chat", url=config.SUPPORT_CHAT),
            InlineKeyboardButton("🗑 Close", callback_data="cb_close"),
        ]
    ])


def help_back_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back to Categories", callback_data="help_main"),
            InlineKeyboardButton("🗑 Close", callback_data="cb_close"),
        ]
    ])
