from pyrogram import types
from py_yt import VideosSearch
from maxmusic.core.bot import bot
from maxmusic.config import config


@bot.on_inline_query()
async def inline_query_handler(_, query: types.InlineQuery):
    text = query.query.strip()
    if not text:
        return await query.answer(
            results=[],
            switch_pm_text="Type song title or YouTube link...",
            switch_pm_parameter="help",
        )

    results = []
    try:
        search = VideosSearch(text, limit=10)
        res = search.result()
        if res and res.get("result"):
            for item in res["result"]:
                title = item.get("title", "Unknown")
                duration = item.get("duration", "0:00")
                link = item.get("link", "")
                thumb = item.get("thumbnails", [{}])[0].get("url", config.DEFAULT_THUMB)
                desc = f"Duration: {duration} | Channel: {item.get('channel', {}).get('name', 'YouTube')}"

                results.append(
                    types.InlineQueryResultArticle(
                        title=title,
                        description=desc,
                        thumb_url=thumb,
                        input_message_content=types.InputTextMessageContent(
                            f"/play {link}"
                        ),
                    )
                )
    except Exception:
        pass

    await query.answer(results=results, cache_time=60)
