from pyrogram import Client, types
from pyrogram.enums import ChatMemberStatus
from maxmusic.core.database import db


async def get_channel_target(chat_id: int, is_channel_mode: bool = False) -> int:
    """If channel mode is requested or active, return linked channel_id or original chat_id."""
    if is_channel_mode:
        linked = db.get_channel(chat_id)
        if linked:
            return linked
    return chat_id


async def verify_channel_admin(app: Client, channel_id: int, user_id: int) -> bool:
    """Verify if the user is an administrator of the linked channel."""
    try:
        member = await app.get_chat_member(channel_id, user_id)
        return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False
