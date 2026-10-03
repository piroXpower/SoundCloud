import time
import psutil
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from config import BOT_NAME, COMMAND_PREFIXES, START_IMAGE_URL
from utils.inline import start_keyboard, help_menu_keyboard, back_to_help_keyboard
from utils.formatters import humanbytes

START_TIME = time.time()

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]
    if len(time_list) == 4:
        ping_time += f"{time_list.pop()}, "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

@Client.on_message(filters.command(["start"], prefixes=COMMAND_PREFIXES))
async def start_handler(client: Client, message: Message):
    bot = await client.get_me()
    chat_type = message.chat.type

    # Group Start
    if chat_type.name in ["GROUP", "SUPERGROUP"]:
        await message.reply_text(
            f"☁️ <b>{BOT_NAME} is Online!</b>\n\n"
            f"<i>Play high-quality music directly from SoundCloud in your group's voice chat!</i>\n"
            f"👉 Use <code>/play [track name or SoundCloud URL]</code> to begin.",
            reply_markup=start_keyboard(bot.username),
        )
        return

    # Private Start
    user_name = message.from_user.first_name if message.from_user else "Music Lover"
    welcome_text = (
        f"👋 <b>Welcome, {user_name}!</b>\n\n"
        f"🎧 I am <b>{BOT_NAME}</b>, your dedicated, lightning-fast Telegram music streamer powered by <b>SoundCloud</b>.\n\n"
        f"✨ <b>Features:</b>\n"
        f" • ☁️ Stream any track or remix directly from SoundCloud\n"
        f" • 🎛️ Full interactive callback buttons (Pause, Skip, Loop, Volume)\n"
        f" • 🎨 Dynamic high-resolution album card thumbnails\n"
        f" • 📜 Advanced smart queue management\n"
        f" • ⚡ Crystal-clear 320kbps audio output\n\n"
        f"<blockquote>Click the buttons below to explore commands or add me to your group!</blockquote>"
    )

    if START_IMAGE_URL:
        await message.reply_photo(
            photo=START_IMAGE_URL,
            caption=welcome_text,
            reply_markup=start_keyboard(bot.username),
        )
    else:
        await message.reply_text(
            welcome_text,
            reply_markup=start_keyboard(bot.username),
        )

@Client.on_message(filters.command(["ping"], prefixes=COMMAND_PREFIXES))
async def ping_handler(client: Client, message: Message):
    start = time.time()
    msg = await message.reply_text("⚡ <i>Pinging SoundCloud server...</i>")
    delta_ms = round((time.time() - start) * 1000, 2)
    uptime = get_readable_time(int(time.time() - START_TIME))
    
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()

    await msg.edit_text(
        f"☁️ <b>SoundCloud Streamer Status</b> 🚀\n\n"
        f"📶 <b>Ping Latency:</b> <code>{delta_ms} ms</code>\n"
        f"⏳ <b>Uptime:</b> <code>{uptime}</code>\n"
        f"💻 <b>CPU Load:</b> <code>{cpu}%</code>\n"
        f"🧠 <b>Memory:</b> <code>{humanbytes(mem.used)} / {humanbytes(mem.total)} ({mem.percent}%)</code>\n"
        f"<blockquote>⚡ <i>Powered by PyTgCalls &amp; Pyrogram</i></blockquote>"
    )

@Client.on_message(filters.command(["help"], prefixes=COMMAND_PREFIXES))
async def help_command(client: Client, message: Message):
    text = (
        "📚 <b>SoundCloud Music Bot — Help Center</b>\n\n"
        "Select a category below to explore available commands and interactive features:"
    )
    await message.reply_text(text, reply_markup=help_menu_keyboard())

# --- Callback Handlers for Help Menus ---

@Client.on_callback_query(filters.regex("^help_main$"))
async def help_main_cb(client: Client, query: CallbackQuery):
    text = (
        "📚 <b>SoundCloud Music Bot — Help Center</b>\n\n"
        "Select a category below to explore available commands and interactive features:"
    )
    await query.message.edit_text(text, reply_markup=help_menu_keyboard())

@Client.on_callback_query(filters.regex("^help_play$"))
async def help_play_cb(client: Client, query: CallbackQuery):
    text = (
        "🎵 <b>Playback & User Commands:</b>\n\n"
        "• <code>/play [name or link]</code> — Search & stream music from SoundCloud.\n"
        "• <code>/sc [query]</code> — Direct SoundCloud search & stream.\n"
        "• <code>/queue</code> — View the upcoming list of tracks in queue.\n"
        "• <code>/song [query]</code> — Download audio or track information.\n"
        "• <code>/ping</code> — Check bot latency, CPU & system uptime.\n\n"
        "<blockquote>💡 <i>You can also use inline buttons directly under the playing track!</i></blockquote>"
    )
    await query.message.edit_text(text, reply_markup=back_to_help_keyboard())

@Client.on_callback_query(filters.regex("^help_admin$"))
async def help_admin_cb(client: Client, query: CallbackQuery):
    text = (
        "🛡 <b>Admin Control Commands:</b>\n\n"
        "• <code>/pause</code> — Pause current audio stream.\n"
        "• <code>/resume</code> — Resume paused audio stream.\n"
        "• <code>/skip</code> — Skip to next track in queue.\n"
        "• <code>/stop</code> or <code>/end</code> — Stop streaming and leave voice chat.\n"
        "• <code>/loop [on/off]</code> — Loop current track or entire queue.\n"
        "• <code>/volume [1-200]</code> — Adjust the voice chat volume.\n"
        "• <code>/clearqueue</code> — Remove all pending tracks in queue.\n"
    )
    await query.message.edit_text(text, reply_markup=back_to_help_keyboard())

@Client.on_callback_query(filters.regex("^help_vc$"))
async def help_vc_cb(client: Client, query: CallbackQuery):
    text = (
        "🎚 <b>Voice Chat & Audio Settings:</b>\n\n"
        "• <code>/mute</code> — Mute the assistant in voice chat.\n"
        "• <code>/unmute</code> — Unmute the assistant in voice chat.\n"
        "• <code>/vol [level]</code> — Quick volume change (e.g. <code>/vol 120</code>).\n"
        "• <code>/reload</code> — Refresh admin cache and voice connection.\n"
    )
    await query.message.edit_text(text, reply_markup=back_to_help_keyboard())

@Client.on_callback_query(filters.regex("^help_sc$"))
async def help_sc_cb(client: Client, query: CallbackQuery):
    text = (
        "☁️ <b>SoundCloud Guide & Tips:</b>\n\n"
        "• Paste any public SoundCloud track link:\n"
        "  <code>/play https://soundcloud.com/artist/track-name</code>\n"
        "• Or search with keyword/artist:\n"
        "  <code>/play Alan Walker Faded remix</code>\n"
        "• High quality 320kbps streams are automatically preferred!\n"
    )
    await query.message.edit_text(text, reply_markup=back_to_help_keyboard())

@Client.on_callback_query(filters.regex("^help_pl$"))
async def help_pl_cb(client: Client, query: CallbackQuery):
    text = (
        "📂 <b>Personal Playlists & History:</b>\n\n"
        "• <code>/playlist</code> — View your saved SoundCloud tracks.\n"
        "• <code>/addplaylist [track/link]</code> — Save track to your playlist.\n"
        "• <code>/delplaylist [number]</code> — Delete track from your playlist.\n"
        "• <code>/playplaylist</code> — Enqueue your entire playlist into the VC.\n"
        "• <code>/history</code> or <code>/recent</code> — View recently streamed tracks with 1-click replay buttons.\n"
    )
    await query.message.edit_text(text, reply_markup=back_to_help_keyboard())

@Client.on_callback_query(filters.regex("^help_extra$"))
async def help_extra_cb(client: Client, query: CallbackQuery):
    text = (
        "🎤 <b>Lyrics, TTS & Utilities:</b>\n\n"
        "• <code>/search [query]</code> — Interactive top-5 SoundCloud search menu.\n"
        "• <code>/song [query]</code> — Download 320kbps MP3 file directly to Telegram.\n"
        "• <code>/lyrics [song]</code> — Instant lyrics reader with auto-track detection.\n"
        "• <code>/tts [text]</code> — Speak text aloud into the group voice chat.\n"
        "• <code>/clean [count]</code> — Delete recent bot service messages in chat.\n"
        "• <code>/trackinfo</code> — View detailed stats about current stream.\n"
        "• <code>/id</code> — Inspect Chat ID and User ID.\n"
    )
    await query.message.edit_text(text, reply_markup=back_to_help_keyboard())

@Client.on_callback_query(filters.regex("^help_home$"))
async def help_home_cb(client: Client, query: CallbackQuery):
    bot = await client.get_me()
    welcome_text = (
        f"🎧 <b>{BOT_NAME} — Main Dashboard</b>\n\n"
        f"Stream unlimited audio from SoundCloud with rich thumbnails & interactive controls."
    )
    await query.message.edit_text(welcome_text, reply_markup=start_keyboard(bot.username))

@Client.on_callback_query(filters.regex("^close_help$"))
async def close_help_cb(client: Client, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception:
        await query.answer("Closed!")
