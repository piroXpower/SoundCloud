import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import COMMAND_PREFIXES
from utils.decorators import is_admin
from core.call import call_manager
from utils.queue import queue_mgr

# chat_id -> asyncio.Task
ACTIVE_TIMERS = {}

async def _sleep_timer_worker(client: Client, chat_id: int, minutes: int):
    try:
        await asyncio.sleep(minutes * 60)
        curr = queue_mgr.get_current(chat_id)
        if curr:
            await call_manager.stop(chat_id)
            await client.send_message(
                chat_id=chat_id,
                text=f"⏰ <b>Sleep Timer Expired!</b>\nStopped voice chat stream after <code>{minutes}</code> minutes. Goodnight! 🌙"
            )
    except asyncio.CancelledError:
        pass
    finally:
        ACTIVE_TIMERS.pop(chat_id, None)

@Client.on_message(filters.command(["sleeptimer", "sleep"], prefixes=COMMAND_PREFIXES) & filters.group)
@is_admin()
async def sleep_timer_cmd(client: Client, message: Message):
    chat_id = message.chat.id

    if len(message.command) < 2:
        buttons = [
            [
                InlineKeyboardButton("⏱ 15 Mins", callback_data=f"sleep_{chat_id}_15"),
                InlineKeyboardButton("⏱ 30 Mins", callback_data=f"sleep_{chat_id}_30"),
                InlineKeyboardButton("⏱ 45 Mins", callback_data=f"sleep_{chat_id}_45"),
            ],
            [
                InlineKeyboardButton("⏱ 60 Mins", callback_data=f"sleep_{chat_id}_60"),
                InlineKeyboardButton("⏱ 90 Mins", callback_data=f"sleep_{chat_id}_90"),
                InlineKeyboardButton("❌ Cancel Timer", callback_data=f"sleep_cancel_{chat_id}"),
            ],
            [
                InlineKeyboardButton("🗑 Close", callback_data=f"ctrl_close_{chat_id}"),
            ]
        ]
        return await message.reply_text(
            "⏰ <b>SoundCloud Sleep Timer:</b>\n"
            "Select how long the bot should play music before automatically disconnecting:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    try:
        mins = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Please enter a valid number of minutes.")

    if mins <= 0 or mins > 360:
        return await message.reply_text("❌ Timer must be between 1 and 360 minutes.")

    # Cancel previous timer if exists
    if chat_id in ACTIVE_TIMERS:
        ACTIVE_TIMERS[chat_id].cancel()

    ACTIVE_TIMERS[chat_id] = asyncio.create_task(_sleep_timer_worker(client, chat_id, mins))
    await message.reply_text(
        f"⏰ <b>Sleep Timer Set!</b>\n"
        f"Playback will automatically stop in <code>{mins}</code> minutes."
    )

@Client.on_callback_query(filters.regex(r"^sleep_(-?\d+)_(\d+)$"))
async def cb_sleep_preset(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    mins = int(query.matches[0].group(2))

    if chat_id in ACTIVE_TIMERS:
        ACTIVE_TIMERS[chat_id].cancel()

    ACTIVE_TIMERS[chat_id] = asyncio.create_task(_sleep_timer_worker(client, chat_id, mins))
    await query.answer(f"Sleep timer set for {mins} minutes.")
    await query.message.edit_text(
        f"⏰ <b>Sleep Timer Active:</b> Voice chat will shut down in <code>{mins}</code> minutes."
    )

@Client.on_callback_query(filters.regex(r"^sleep_cancel_(-?\d+)$"))
async def cb_sleep_cancel(client: Client, query: CallbackQuery):
    chat_id = int(query.matches[0].group(1))
    if chat_id in ACTIVE_TIMERS:
        ACTIVE_TIMERS[chat_id].cancel()
        ACTIVE_TIMERS.pop(chat_id, None)
        await query.answer("Sleep timer cancelled!")
        await query.message.edit_text("⏰ <b>Sleep Timer Cancelled.</b> Stream will continue normally.")
    else:
        await query.answer("No active sleep timer found.", show_alert=True)
