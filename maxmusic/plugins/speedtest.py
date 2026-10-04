import asyncio
import speedtest
from pyrogram import filters, types
from maxmusic.core.bot import bot
from maxmusic.helpers.filters import sudo_only


def _run_speedtest():
    st = speedtest.Speedtest()
    st.get_best_server()
    st.download()
    st.upload()
    return st.results.dict()


@bot.on_message(filters.command(["speedtest"]) & sudo_only)
async def speedtest_command(_, message: types.Message):
    status_msg = await message.reply_text("⚡ <i>Running network speedtest... Please wait...</i>")
    try:
        results = await asyncio.to_thread(_run_speedtest)
        download_mbs = round(results["download"] / 10**6, 2)
        upload_mbs = round(results["upload"] / 10**6, 2)
        ping_ms = round(results["ping"], 2)
        server_info = results.get("server", {})

        text = (
            f"🚀 <b>Network Speedtest Results</b>\n\n"
            f"📥 <b>Download:</b> {download_mbs} Mbps\n"
            f"📤 <b>Upload:</b> {upload_mbs} Mbps\n"
            f"📶 <b>Ping:</b> {ping_ms} ms\n"
            f"🏢 <b>Sponsor:</b> {server_info.get('sponsor', 'Unknown')}\n"
            f"🌍 <b>Location:</b> {server_info.get('name', 'Unknown')}, {server_info.get('country', '')}\n"
        )
        await status_msg.edit_text(text)
    except Exception as e:
        await status_msg.edit_text(f"❌ Speedtest failed: {e}")
