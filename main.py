from telethon import TelegramClient
from dotenv import load_dotenv
import os

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient('parser_session', API_ID, API_HASH)

async def main():
    target_chat = 'telegram'
    print("Getting...")

    async for message in client.iter_messages(target_chat, limit = 30):
        if message.text:
            print('-' * 30)
            print(f"📅 Дата: {message.date}")
            print(f"💬 Текст: {message.text[:100]}...")

with client:
    client.loop.run_until_complete(main())

