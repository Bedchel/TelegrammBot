import asyncio
from telethon import TelegramClient

api_id = 37587197
api_hash = 'ebe579cce7e826af00b4771f6837908d'

# Указали правильные названия чатов
CHATS = ['@deltarune_cases_bot', 'Ферма tanatolii']
COMMAND = "/open DELTARUNE"

async def main():
    # Файлы лежат в папке api, поэтому путь 'api/my_session'
    async with TelegramClient('api/my_session', api_id, api_hash) as client:
        print("Запуск отправки...")
        for chat in CHATS:
            try:
                await client.send_message(chat, COMMAND)
                print(f"Сообщение успешно отправлено в {chat}")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"Не удалось отправить в {chat}: {e}")

if __name__ == '__main__':
    asyncio.run(main())
