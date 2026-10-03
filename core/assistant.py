from pyrogram import Client
from config import API_ID, API_HASH, SESSION_STRING

class AssistantClient(Client):
    def __init__(self):
        super().__init__(
            name="SoundCloudAssistant",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=SESSION_STRING,
            in_memory=True,
        )

    async def start(self):
        if not SESSION_STRING:
            print("⚠️ [Warning] SESSION_STRING is empty! Voice calls will not function until provided.")
            return
        await super().start()
        me = await self.get_me()
        print(f"🎙️ [Assistant Started]: @{me.username} ({me.first_name})")

    async def stop(self, *args):
        if SESSION_STRING:
            await super().stop()
            print("🛑 [Assistant Stopped]")

userbot = AssistantClient()
