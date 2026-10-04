from pyrogram import filters, types
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from maxmusic.config import config
from maxmusic.core.database import db

# In-memory admin cache to prevent spamming Telegram get_chat_member
_ADMIN_CACHE = {}


async def is_admin_or_auth(client, chat_id: int, user_id: int) -> bool:
    if user_id == config.OWNER_ID or db.is_sudo(user_id):
        return True

    # Check authorized users (DJ role)
    auth_users = await db.get_auth_users(chat_id)
    if user_id in auth_users:
        return True

    # Check Telegram Admin Cache
    admins = _ADMIN_CACHE.get(chat_id)
    if admins is None:
        admins = set()
        try:
            async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
                if member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
                    admins.add(member.user.id)
            _ADMIN_CACHE[chat_id] = admins
        except Exception:
            return False

    return user_id in admins


def reload_admin_cache(chat_id: int):
    _ADMIN_CACHE.pop(chat_id, None)


async def admin_or_auth_check(_, client, message: types.Message) -> bool:
    if not message.from_user:
        return False
    return await is_admin_or_auth(client, message.chat.id, message.from_user.id)


admin_or_auth = filters.create(admin_or_auth_check)


async def sudo_check(_, __, message: types.Message) -> bool:
    if not message.from_user:
        return False
    return db.is_sudo(message.from_user.id)


sudo_only = filters.create(sudo_check)


async def owner_check(_, __, message: types.Message) -> bool:
    if not message.from_user:
        return False
    return message.from_user.id == config.OWNER_ID


owner_only = filters.create(owner_check)
