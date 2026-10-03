import asyncio
import time
from pyrogram import Client
from utils.queue import queue_mgr
from core.call import call_manager

# chat_id -> timestamp when playback stopped/paused
IDLE_TRACKER = {}

async def auto_leave_worker(client: Client):
    """Background task to auto-leave inactive voice chats after 5 minutes of silence."""
    while True:
        await asyncio.sleep(60) # Check every 60 seconds
        now = time.time()

        for chat_id, track in list(queue_mgr._current.items()):
            if not track:
                if chat_id not in IDLE_TRACKER:
                    IDLE_TRACKER[chat_id] = now
                elif now - IDLE_TRACKER[chat_id] > 300: # 5 minutes idle
                    try:
                        await call_manager.stop(chat_id)
                        await client.send_message(
                            chat_id=chat_id,
                            text="💤 <b>Voice Chat Inactive:</b> Assistant left the voice chat due to 5 minutes of inactivity."
                        )
                    except Exception:
                        pass
                    IDLE_TRACKER.pop(chat_id, None)
            else:
                IDLE_TRACKER.pop(chat_id, None)

# Automatically start worker when bot connects
@Client.on_message()
async def _init_autoleave(client: Client, message):
    if not getattr(client, "_autoleave_started", False):
        client._autoleave_started = True
        asyncio.create_task(auto_leave_worker(client))
    message.continue_propagation()
