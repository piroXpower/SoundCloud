import asyncio
from pyrogram import Client

async def main():
    print("=" * 50)
    print("  Pyrogram Session String Generator for Assistant")
    print("=" * 50)
    
    api_id = input("Enter your API_ID: ").strip()
    api_hash = input("Enter your API_HASH: ").strip()

    async with Client(name="AssistantSession", api_id=int(api_id), api_hash=api_hash, in_memory=True) as app:
        session_str = await app.export_session_string()
        print("\n" + "=" * 50)
        print("YOUR SESSION STRING (Keep this secret!):")
        print("=" * 50)
        print(session_str)
        print("=" * 50)
        print("\nCopy this string and paste it into your .env as SESSION_STRING")

if __name__ == "__main__":
    asyncio.run(main())
