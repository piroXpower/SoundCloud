import aiohttp
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.queue import queue_mgr


@bot.on_message(filters.command(["lyrics", "lyric"]))
async def lyrics_command(_, message: types.Message):
    query = ""
    if len(message.command) > 1:
        query = " ".join(message.command[1:]).strip()
    else:
        # Check currently playing track in chat
        current = queue_mgr.current(message.chat.id)
        if current:
            query = current.title

    if not query:
        return await message.reply_text("Usage: <code>/lyrics [Song Title]</code>")

    status_msg = await message.reply_text(f"🔎 <i>Searching lyrics for:</i> <b>{query}</b>...")

    url = f"https://api.popcat.xyz/lyrics?song={query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = data.get("lyrics")
                    title = data.get("title", query)
                    artist = data.get("artist", "Unknown")

                    if lyrics:
                        header = f"📜 <b>Lyrics for {title}</b> by <i>{artist}</i>:\n\n"
                        full_text = header + lyrics
                        if len(full_text) > 4000:
                            full_text = full_text[:4000] + "\n\n...[Truncated]"
                        return await status_msg.edit_text(full_text)
    except Exception:
        pass

    await status_msg.edit_text(f"❌ Could not find lyrics for <b>{query}</b>.")
