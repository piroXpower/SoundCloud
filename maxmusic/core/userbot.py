import logging
from typing import Dict, List, Optional
from pyrogram import Client
from maxmusic.config import config

logger = logging.getLogger(__name__)


class Userbot:
    def __init__(self):
        self.clients: List[Client] = []
        self._chat_client_map: Dict[int, Client] = {}

        sessions = [
            ("Assistant 1", config.SESSION1),
            ("Assistant 2", config.SESSION2),
            ("Assistant 3", config.SESSION3),
        ]

        self._active_sessions = [(name, s) for name, s in sessions if s]

    async def boot(self):
        for idx, (name, session_str) in enumerate(self._active_sessions, start=1):
            try:
                client = Client(
                    name=f"MaxAssistant{idx}",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=session_str,
                    in_memory=True,
                )
                await client.start()
                me = await client.get_me()
                client.me = me
                client.assistant_num = idx
                self.clients.append(client)
                logger.info(f"{name} online as @{me.username or me.id}")
            except Exception as e:
                logger.error(f"Failed to start {name}: {e}")

        if not self.clients:
            raise SystemExit("No assistant clients could be started! Check your SESSION strings.")

    async def exit(self):
        for client in self.clients:
            try:
                await client.stop()
            except Exception:
                pass
        logger.info("All assistant clients stopped.")

    def get_assistant(self, chat_id: int) -> Client:
        if chat_id in self._chat_client_map:
            return self._chat_client_map[chat_id]
        # Distribute round-robin or hash-based
        client = self.clients[abs(chat_id) % len(self.clients)]
        self._chat_client_map[chat_id] = client
        return client

    async def join_assistant(self, chat_id: int, chat_username: str | None = None) -> bool:
        client = self.get_assistant(chat_id)
        try:
            if chat_username:
                await client.join_chat(chat_username)
            else:
                await client.get_chat(chat_id)
            return True
        except Exception as e:
            logger.warning(f"Assistant could not join chat {chat_id}: {e}")
            return False


userbot = Userbot()
