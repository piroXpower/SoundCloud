import math
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.queue import queue_mgr
from maxmusic.helpers.buttons import queue_markup


def get_queue_page_text(chat_id: int, page: int = 1, per_page: int = 5) -> tuple[str, int]:
    current = queue_mgr.current(chat_id)
    tracks = queue_mgr.get_queue(chat_id)

    total_pages = max(1, math.ceil(len(tracks) / per_page))
    page = max(1, min(page, total_pages))

    text = "📜 <b>Current Chat Queue</b>\n\n"
    if current:
        text += (
            f"🎵 <b>Now Playing:</b>\n"
            f"• <b>Title:</b> {current.title}\n"
            f"• <b>Duration:</b> {current.duration} | <b>By:</b> {current.requester}\n\n"
        )
    else:
        text += "<i>No song is currently playing.</i>\n\n"

    if not tracks:
        text += "<i>Queue is empty.</i>"
        return text, total_pages

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_tracks = tracks[start_idx:end_idx]

    text += f"📑 <b>Queued Tracks (Page {page}/{total_pages}):</b>\n"
    for i, t in enumerate(page_tracks, start=start_idx + 1):
        text += f"<b>{i}.</b> {t.title} ({t.duration}) - {t.requester}\n"

    return text, total_pages


@bot.on_message(filters.command(["queue", "q"]) & filters.group)
async def queue_command(_, message: types.Message):
    chat_id = message.chat.id
    text, total_pages = get_queue_page_text(chat_id, page=1)
    markup = queue_markup(chat_id, page=1, total_pages=total_pages)
    await message.reply_text(text, reply_markup=markup, disable_web_page_preview=True)
