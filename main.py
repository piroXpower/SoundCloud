import asyncio
from pyrogram import idle
from core.bot import app
from core.assistant import userbot
from core.call import call_manager
from config import BOT_NAME

BANNER = r"""
  ___                  _ _____ _             _ 
 / __| ___ _  _ _ _  __| / ___| |___ _  _ __| |
 \__ \/ _ \ || | ' \/ _` \___ \ / _ \ || / _` |
 |___/\___/\_,_|_||_\__,_|____/_\___/\_,_\__,_|
           Music Bot for Telegram (SoundCloud Edition)
"""

async def start_bot():
    print(BANNER)
    print(f"🚀 Starting {BOT_NAME}...")

    # Start Bot client
    await app.start()
    
    # Start Assistant userbot client (for voice calls)
    await userbot.start()
    
    # Start PyTgCalls
    await call_manager.start()

    print(f"✅ {BOT_NAME} is fully online and listening for voice calls!")
    
    # Idle until termination
    await idle()

    # Graceful shutdown
    print("🛑 Shutting down bot and voice calls...")
    await userbot.stop()
    await app.stop()
    print("👋 Goodbye!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bot())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped by user.")
