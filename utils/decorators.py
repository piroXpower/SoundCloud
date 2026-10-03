from functools import wraps
from pyrogram.types import CallbackQuery, Message
from pyrogram.enums import ChatMemberStatus
from config import SUDO_USERS

# chat_id -> set of authorized user_ids
AUTH_USERS = {}

def is_admin():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, update, *args, **kwargs):
            user_id = None
            chat_id = None

            if isinstance(update, Message):
                if not update.from_user:
                    return await func(client, update, *args, **kwargs)
                user_id = update.from_user.id
                chat_id = update.chat.id
            elif isinstance(update, CallbackQuery):
                user_id = update.from_user.id
                chat_id = update.message.chat.id if update.message else None

            # Always allow sudo/owner
            if user_id in SUDO_USERS:
                return await func(client, update, *args, **kwargs)

            # Check authorized users for this chat
            if chat_id and user_id in AUTH_USERS.get(chat_id, set()):
                return await func(client, update, *args, **kwargs)

            # Check group admin status
            if chat_id and chat_id < 0:
                try:
                    member = await client.get_chat_member(chat_id, user_id)
                    if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                        return await func(client, update, *args, **kwargs)
                except Exception:
                    pass

            # If user is not authorized
            if isinstance(update, CallbackQuery):
                return await update.answer(
                    "⚠️ Only group administrators or sudo users can use these controls!",
                    show_alert=True,
                )
            elif isinstance(update, Message):
                return await update.reply_text(
                    "❌ **Permission Denied**: You need to be an administrator to run this command."
                )

        return wrapper
    return decorator
