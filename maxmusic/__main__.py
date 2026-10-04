import asyncio
import importlib
import logging
import signal
from contextlib import suppress

from maxmusic import bot, calls, config, db, logger, userbot
from maxmusic.plugins import ALL_MODULES


async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()


async def main():
    logger.info("==========================================")
    logger.info(f" Starting {config.BOT_NAME}...")
    logger.info("==========================================")

    # 1. Validate configuration
    config.check()

    # 2. Connect Database
    await db.connect()

    # 3. Boot Bot Client
    await bot.boot()

    # 4. Boot Assistant Userbots
    await userbot.boot()

    # 5. Boot WebRTC PyTgCalls Engine
    await calls.boot()

    # 6. Load all Plugins
    loaded_count = 0
    for module in ALL_MODULES:
        try:
            importlib.import_module(f"maxmusic.plugins.{module}")
            loaded_count += 1
        except Exception as e:
            logger.error(f"Failed to load plugin '{module}': {e}")

    logger.info(f"Successfully loaded {loaded_count}/{len(ALL_MODULES)} plugins.")
    logger.info("==========================================")
    logger.info(f" {config.BOT_NAME} is Online & Ready!")
    logger.info("==========================================")

    # Keep running until interrupt
    await idle()

    # Graceful shutdown
    logger.info("Shutting down bot services...")
    for cid in list(db.active_calls.keys()):
        with suppress(Exception):
            await calls.stop(cid)

    with suppress(Exception):
        await bot.exit()
    with suppress(Exception):
        await userbot.exit()
    with suppress(Exception):
        await db.close()

    logger.info("Shutdown completed cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
