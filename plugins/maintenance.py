from pyrogram import Client, filters
from pyrogram.types import Message
from config import SUDO_USERS, COMMAND_PREFIXES

MAINTENANCE_STATE = {"enabled": False, "reason": "Scheduled Server Upgrade"}

def is_maintenance() -> bool:
    return MAINTENANCE_STATE["enabled"]

@Client.on_message(filters.command(["maintenance"], prefixes=COMMAND_PREFIXES) & filters.user(SUDO_USERS))
async def maintenance_cmd(client: Client, message: Message):
    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg in ["on", "enable", "start"]:
            MAINTENANCE_STATE["enabled"] = True
            if len(message.command) > 2:
                MAINTENANCE_STATE["reason"] = " ".join(message.command[2:])
            return await message.reply_text(
                f"🚧 <b>Maintenance Mode Enabled!</b>\n"
                f"Reason: <code>{MAINTENANCE_STATE['reason']}</code>\n"
                f"Regular users will be blocked from running commands."
            )
        elif arg in ["off", "disable", "stop"]:
            MAINTENANCE_STATE["enabled"] = False
            return await message.reply_text("✅ <b>Maintenance Mode Disabled!</b> Bot is fully operational.")

    status = "Active 🚧" if MAINTENANCE_STATE["enabled"] else "Disabled ✅"
    await message.reply_text(
        f"🛠️ <b>Maintenance System:</b>\n\n"
        f"• <b>Status:</b> <code>{status}</code>\n"
        f"• <b>Reason:</b> <code>{MAINTENANCE_STATE['reason']}</code>\n\n"
        f"Usage: <code>/maintenance [on / off] [reason]</code>"
    )
