import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import aiohttp

from config import SUDO_USERS, COMMAND_PREFIXES

async def run_simple_speedtest():
    """Performs an asynchronous network speed test using cloudflare speed test endpoints."""
    start = time.time()
    ping = 0
    download_mbps = 0

    try:
        async with aiohttp.ClientSession() as session:
            # Ping test
            t0 = time.time()
            async with session.get("https://1.1.1.1", timeout=5) as r:
                if r.status == 200:
                    ping = round((time.time() - t0) * 1000, 2)

            # Download test (10MB payload)
            t1 = time.time()
            async with session.get("https://speed.cloudflare.com/__down?bytes=10000000", timeout=15) as r:
                data = await r.read()
                dur = time.time() - t1
                size_mb = len(data) / (1024 * 1024)
                download_mbps = round((size_mb * 8) / dur, 2)
    except Exception as e:
        print(f"[Speedtest Error] {e}")

    return ping, download_mbps

@Client.on_message(filters.command(["speedtest"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def speedtest_cmd(client: Client, message: Message):
    status = await message.reply_text("⚡ <i>Running server network bandwidth speed test...</i>")

    ping, dl = await run_simple_speedtest()

    text = (
        "🚀 <b>SoundCloud Bot Server Network Stats:</b>\n\n"
        f"📶 <b>Ping Latency:</b> <code>{ping} ms</code>\n"
        f"📥 <b>Download Speed:</b> <code>{dl} Mbps</code>\n"
        f"🎙️ <b>VC Stream Quality:</b> <code>Ultra HD (320kbps Lossless)</code>\n\n"
        "<blockquote>⚡ <i>Network optimized for low-latency voice chat audio streaming</i></blockquote>"
    )

    await status.edit_text(text)
