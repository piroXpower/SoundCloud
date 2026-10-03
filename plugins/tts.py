import os
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

from config import COMMAND_PREFIXES
from core.call import call_manager
from utils.queue import queue_mgr
from utils.formatters import clean_html

TTS_DIR = "/tmp/sc_tts"
os.makedirs(TTS_DIR, exist_ok=True)

async def generate_speech(text: str, lang: str = "en") -> str:
    encoded_text = text.replace(" ", "%20")
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl={lang}&client=tw-ob"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    file_path = os.path.join(TTS_DIR, f"tts_{abs(hash(text)) % 100000}.mp3")
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(file_path, "wb") as f:
                    f.write(await resp.read())
                return file_path
    return ""

@Client.on_message(filters.command(["tts", "say", "speak"], prefixes=COMMAND_PREFIXES) & filters.group)
async def tts_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("🗣️ <b>Usage:</b> <code>/tts [text to speak in voice chat]</code>")

    text = " ".join(message.command[1:]) if len(message.command) > 1 else message.reply_to_message.text.strip()
    if len(text) > 200:
        return await message.reply_text("⚠️ Text is too long (maximum 200 characters).")

    status = await message.reply_text("🗣️ <i>Synthesizing speech...</i>")

    try:
        audio_file = await generate_speech(text)
        if not audio_file or not os.path.exists(audio_file):
            return await status.edit_text("❌ Failed to synthesize audio speech.")

        chat_id = message.chat.id
        await status.edit_text("🎙️ <i>Broadcasting voice message in VC...</i>")

        # Play TTS audio in call
        await call_manager.play_or_change(chat_id, audio_file)

        await status.edit_text(f"🗣️ <b>Announced in Voice Chat:</b>\n<blockquote>\"{clean_html(text)}\"</blockquote>")

    except Exception as e:
        await status.edit_text(f"❌ <b>TTS Error:</b> <code>{clean_html(str(e))}</code>")
