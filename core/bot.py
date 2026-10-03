from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME

class MusicBot(Client):
    def __init__(self):
        super().__init__(
            name="SoundCloudMusicBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            in_memory=True,
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        print(f"✨ [Bot Started]: @{me.username} ({me.first_name})")

    async def stop(self, *args):
        await super().stop()
        print("🛑 [Bot Stopped]")

app = MusicBot()
