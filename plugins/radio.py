from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.queue import queue_mgr
from core.call import call_manager
from utils.inline import player_keyboard

RADIO_STATIONS = {
    "lofi": {
        "name": "☕ 24/7 Lofi Hip Hop Beats",
        "url": "http://stream.zeno.fm/f3wvbbqmdg8uv",
        "thumb": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=600",
    },
    "synthwave": {
        "name": "🌆 80s Synthwave & Retrowave",
        "url": "http://stream.zeno.fm/7xvh81dwtg8uv",
        "thumb": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=600",
    },
    "chill": {
        "name": "🍃 Chillout & Lounge Ambient",
        "url": "http://stream.zeno.fm/0r0xa792kwzuv",
        "thumb": "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=600",
    },
    "edm": {
        "name": "⚡ Electronic Dance Music (EDM)",
        "url": "http://stream.zeno.fm/f3wvbbqmdg8uv",
        "thumb": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=600",
    },
    "rock": {
        "name": "🎸 Classic Rock Hits",
        "url": "http://stream.zeno.fm/3r8v4wqwtg8uv",
        "thumb": "https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?w=600",
    },
}

@Client.on_message(filters.command(["radio", "live"], prefixes=COMMAND_PREFIXES) & filters.group)
async def radio_cmd(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton("☕ Lofi Hip Hop", callback_data=f"radio_lofi_{message.chat.id}"),
            InlineKeyboardButton("🌆 Synthwave", callback_data=f"radio_synthwave_{message.chat.id}"),
        ],
        [
            InlineKeyboardButton("🍃 Chillout Lounge", callback_data=f"radio_chill_{message.chat.id}"),
            InlineKeyboardButton("⚡ EDM Dance", callback_data=f"radio_edm_{message.chat.id}"),
        ],
        [
            InlineKeyboardButton("🎸 Classic Rock", callback_data=f"radio_rock_{message.chat.id}"),
        ],
        [
            InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{message.chat.id}"),
        ]
    ]

    await message.reply_text(
        "📻 <b>24/7 Live Radio Stations:</b>\n"
        "Select an uninterrupted, commercial-free live stream below to broadcast in your voice chat:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^radio_([a-z]+)_(-?\d+)$"))
async def cb_radio_play(client: Client, query: CallbackQuery):
    station_key = query.matches[0].group(1)
    chat_id = int(query.matches[0].group(2))

    station = RADIO_STATIONS.get(station_key)
    if not station:
        return await query.answer("Station not found!", show_alert=True)

    await query.answer(f"Connecting to {station['name']}...")
    status = await client.send_message(chat_id, f"📻 <i>Connecting to {station['name']}...</i>")

    track_obj = {
        "title": station["name"],
        "uploader": "24/7 Live Web Radio",
        "duration_sec": 0,
        "url": station["url"],
        "stream_url": station["url"],
        "thumbnail": station["thumb"],
        "requester_mention": query.from_user.mention,
        "requester_id": query.from_user.id,
    }

    try:
        await call_manager.play_or_change(chat_id, station["url"])
        queue_mgr.set_current(chat_id, track_obj)

        caption = (
            f"📻 <b>Now Live on Radio:</b>\n\n"
            f"📡 <b>Station:</b> <code>{station['name']}</code>\n"
            f"🔴 <b>Status:</b> <code>24/7 Continuous Broadcast</code>\n"
            f"🎧 <b>Tuned in by:</b> {query.from_user.mention}\n\n"
            f"<blockquote>⚡ <i>Powered by PyTgCalls</i></blockquote>"
        )

        keyboard = player_keyboard(
            chat_id=chat_id,
            is_paused=False,
            loop_mode="none",
            sc_url="",
        )

        await status.delete()
        await client.send_message(chat_id, text=caption, reply_markup=keyboard)

    except Exception as e:
        await status.edit_text(f"❌ <b>Radio Connection Error:</b> <code>{e}</code>")
