import logging
import time
from typing import Dict, List, Set, Any
from pymongo import AsyncMongoClient
from maxmusic.config import config

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self._client: AsyncMongoClient | None = None
        self._db = None

        # Collections
        self.sudoers_col = None
        self.bl_chats_col = None
        self.bl_users_col = None
        self.auth_col = None
        self.lang_col = None
        self.channel_col = None
        self.settings_col = None
        self.gban_col = None
        self.stats_col = None

        # High-Speed In-Memory Caches
        self.sudoers: Set[int] = set()
        self.blacklisted_chats: Set[int] = set()
        self.blacklisted_users: Set[int] = set()
        self.gbanned_users: Set[int] = set()
        self.auth_cache: Dict[int, Set[int]] = {}
        self.lang_cache: Dict[int, str] = {}
        self.channel_cache: Dict[int, int] = {}
        self.settings_cache: Dict[int, Dict[str, Any]] = {}
        self.active_calls: Dict[int, Dict[str, Any]] = {}
        self.loop_cache: Dict[int, int] = {}
        self.maintenance_mode: bool = False

    async def connect(self):
        start = time.time()
        self._client = AsyncMongoClient(config.MONGO_URL, serverSelectionTimeoutMS=5000)
        self._db = self._client[config.DB_NAME]

        # Init collections
        self.sudoers_col = self._db.sudoers
        self.bl_chats_col = self._db.blacklisted_chats
        self.bl_users_col = self._db.blacklisted_users
        self.auth_col = self._db.authorized_users
        self.lang_col = self._db.languages
        self.channel_col = self._db.channel_play
        self.settings_col = self._db.chat_settings
        self.gban_col = self._db.gban
        self.stats_col = self._db.stats

        try:
            await self._client.admin.command("ping")
            logger.info(f"Connected to MongoDB ({time.time() - start:.2f}s)")
            await self._load_caches()
        except Exception as e:
            logger.critical(f"Failed to connect to MongoDB: {e}")
            raise SystemExit("MongoDB connection failed") from e

    async def close(self):
        if self._client:
            await self._client.close()
            logger.info("MongoDB connection closed.")

    async def _load_caches(self):
        # Load Sudoers
        self.sudoers.add(config.OWNER_ID)
        cursor = self.sudoers_col.find({})
        async for doc in cursor:
            self.sudoers.add(doc["user_id"])

        # Load Blacklists
        async for doc in self.bl_chats_col.find({}):
            self.blacklisted_chats.add(doc["chat_id"])
        async for doc in self.bl_users_col.find({}):
            self.blacklisted_users.add(doc["user_id"])
        async for doc in self.gban_col.find({}):
            self.gbanned_users.add(doc["user_id"])

        # Load Channel Play links
        async for doc in self.channel_col.find({}):
            self.channel_cache[doc["chat_id"]] = doc["channel_id"]

        # Load Maintenance mode
        maint_doc = await self._db.system.find_one({"_id": "maintenance"})
        if maint_doc:
            self.maintenance_mode = maint_doc.get("enabled", False)

        logger.info(
            f"Cached: {len(self.sudoers)} sudoers, {len(self.blacklisted_chats)} blocked chats, "
            f"{len(self.blacklisted_users)} blocked users, {len(self.channel_cache)} channel links."
        )

    # --- Sudoers ---
    def is_sudo(self, user_id: int) -> bool:
        return user_id in self.sudoers or user_id == config.OWNER_ID

    async def add_sudo(self, user_id: int) -> bool:
        if user_id in self.sudoers:
            return False
        self.sudoers.add(user_id)
        await self.sudoers_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
        return True

    async def remove_sudo(self, user_id: int) -> bool:
        if user_id not in self.sudoers or user_id == config.OWNER_ID:
            return False
        self.sudoers.remove(user_id)
        await self.sudoers_col.delete_one({"user_id": user_id})
        return True

    def get_sudoers(self) -> Set[int]:
        return set(self.sudoers)

    # --- Blacklist Chats & Users ---
    def is_chat_blacklisted(self, chat_id: int) -> bool:
        return chat_id in self.blacklisted_chats

    async def blacklist_chat(self, chat_id: int, reason: str = "") -> bool:
        self.blacklisted_chats.add(chat_id)
        await self.bl_chats_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "reason": reason}},
            upsert=True
        )
        return True

    async def whitelist_chat(self, chat_id: int) -> bool:
        self.blacklisted_chats.discard(chat_id)
        await self.bl_chats_col.delete_one({"chat_id": chat_id})
        return True

    def is_user_blacklisted(self, user_id: int) -> bool:
        return user_id in self.blacklisted_users or user_id in self.gbanned_users

    async def blacklist_user(self, user_id: int, reason: str = "") -> bool:
        self.blacklisted_users.add(user_id)
        await self.bl_users_col.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "reason": reason}},
            upsert=True
        )
        return True

    async def whitelist_user(self, user_id: int) -> bool:
        self.blacklisted_users.discard(user_id)
        await self.bl_users_col.delete_one({"user_id": user_id})
        return True

    # --- GBan ---
    def is_gbanned(self, user_id: int) -> bool:
        return user_id in self.gbanned_users

    async def gban_user(self, user_id: int, reason: str = ""):
        self.gbanned_users.add(user_id)
        await self.gban_col.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "reason": reason}},
            upsert=True
        )

    async def ungban_user(self, user_id: int):
        self.gbanned_users.discard(user_id)
        await self.gban_col.delete_one({"user_id": user_id})

    # --- Authorized Users (DJ per group) ---
    async def get_auth_users(self, chat_id: int) -> Set[int]:
        if chat_id in self.auth_cache:
            return self.auth_cache[chat_id]
        doc = await self.auth_col.find_one({"chat_id": chat_id})
        users = set(doc.get("users", [])) if doc else set()
        self.auth_cache[chat_id] = users
        return users

    async def add_auth_user(self, chat_id: int, user_id: int) -> bool:
        auths = await self.get_auth_users(chat_id)
        if user_id in auths:
            return False
        auths.add(user_id)
        await self.auth_col.update_one(
            {"chat_id": chat_id},
            {"$addToSet": {"users": user_id}},
            upsert=True
        )
        return True

    async def remove_auth_user(self, chat_id: int, user_id: int) -> bool:
        auths = await self.get_auth_users(chat_id)
        if user_id not in auths:
            return False
        auths.discard(user_id)
        await self.auth_col.update_one(
            {"chat_id": chat_id},
            {"$pull": {"users": user_id}}
        )
        return True

    # --- Channel Play ---
    def get_channel(self, chat_id: int) -> int | None:
        return self.channel_cache.get(chat_id)

    async def set_channel(self, chat_id: int, channel_id: int):
        self.channel_cache[chat_id] = channel_id
        await self.channel_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"channel_id": channel_id}},
            upsert=True
        )

    async def remove_channel(self, chat_id: int):
        self.channel_cache.pop(chat_id, None)
        await self.channel_col.delete_one({"chat_id": chat_id})

    # --- Language ---
    async def get_lang(self, chat_id: int) -> str:
        if chat_id in self.lang_cache:
            return self.lang_cache[chat_id]
        doc = await self.lang_col.find_one({"chat_id": chat_id})
        lang_code = doc.get("lang", config.LANG_CODE) if doc else config.LANG_CODE
        self.lang_cache[chat_id] = lang_code
        return lang_code

    async def set_lang(self, chat_id: int, lang_code: str):
        self.lang_cache[chat_id] = lang_code
        await self.lang_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"lang": lang_code}},
            upsert=True
        )

    # --- Chat Settings ---
    async def get_chat_settings(self, chat_id: int) -> Dict[str, Any]:
        if chat_id in self.settings_cache:
            return self.settings_cache[chat_id]
        doc = await self.settings_col.find_one({"chat_id": chat_id})
        settings = doc.get("settings", {
            "play_mode": "Everyone",  # Everyone or Admins
            "play_type": "Both",      # Audio / Video / Both
            "clean_mode": True,
            "quality": "high",
        }) if doc else {
            "play_mode": "Everyone",
            "play_type": "Both",
            "clean_mode": True,
            "quality": "high",
        }
        self.settings_cache[chat_id] = settings
        return settings

    async def update_chat_setting(self, chat_id: int, key: str, value: Any):
        settings = await self.get_chat_settings(chat_id)
        settings[key] = value
        self.settings_cache[chat_id] = settings
        await self.settings_col.update_one(
            {"chat_id": chat_id},
            {"$set": {f"settings.{key}": value}},
            upsert=True
        )

    # --- Active Calls & Loops ---
    def is_call_active(self, chat_id: int) -> bool:
        return chat_id in self.active_calls

    def set_call_active(self, chat_id: int, data: Dict[str, Any] | None = None):
        self.active_calls[chat_id] = data or {"active": True, "paused": False}

    def remove_call_active(self, chat_id: int):
        self.active_calls.pop(chat_id, None)
        self.loop_cache.pop(chat_id, None)

    def get_loop(self, chat_id: int) -> int:
        return self.loop_cache.get(chat_id, 0)

    def set_loop(self, chat_id: int, count: int):
        self.loop_cache[chat_id] = count

    # --- Maintenance Mode ---
    async def set_maintenance(self, enabled: bool):
        self.maintenance_mode = enabled
        await self._db.system.update_one(
            {"_id": "maintenance"},
            {"$set": {"enabled": enabled}},
            upsert=True
        )


db = Database()
