import asyncio
from pyrogram import Client
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import yt_dlp
from utils.formatters import clean_html, format_duration

def _inline_search(query: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "noplaylist": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            res = ydl.extract_info(f"scsearch5:{query}", download=False)
            if not res or "entries" not in res:
                return []
            return res["entries"][:5]
        except Exception:
            return []

@Client.on_inline_query()
async def inline_search_handler(client: Client, inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query:
        return await inline_query.answer(
            results=[],
            switch_pm_text="☁️ Type a song title to search SoundCloud...",
            switch_pm_parameter="help",
        )

    entries = await asyncio.to_thread(_inline_search, query)
    results = []

    for entry in entries:
        title = entry.get("title", "Unknown")
        uploader = entry.get("uploader") or "SoundCloud Artist"
        duration_sec = int(entry.get("duration") or 0)
        url = entry.get("url") or entry.get("webpage_url") or "https://soundcloud.com"
        thumb = entry.get("thumbnail") or "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400"

        text = (
            f"☁️ <b>SoundCloud Track:</b>\n\n"
            f"🎵 <b>Title:</b> <a href=\"{url}\">{clean_html(title)}</a>\n"
            f"👤 <b>Artist:</b> <code>{clean_html(uploader)}</code>\n"
            f"⏱ <b>Duration:</b> <code>{format_duration(duration_sec)}</code>\n"
        )

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("☁️ Listen on SoundCloud", url=url)]
        ])

        results.append(
            InlineQueryResultArticle(
                id=str(entry.get("id")),
                title=title,
                description=f"by {uploader} • {format_duration(duration_sec)}",
                thumb_url=thumb,
                input_message_content=InputTextMessageContent(
                    text,
                    disable_web_page_preview=False,
                ),
                reply_markup=reply_markup,
            )
        )

    await inline_query.answer(results=results, cache_time=60)
