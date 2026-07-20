import asyncio
from telethon import TelegramClient

api_id = 37587197
api_hash = 'ebe579cce7e826af00b4771f6837908d'
CHATS = ['@deltarune_cases_bot']
COMMAND = "/open DELTARUNE"

async def main():
    async with TelegramClient('api/my_session', api_id, api_hash) as client:
        while True:  # Бесконечный цикл
            print("Запуск круга отправки...")
            for chat in CHATS:
                try:
                    await client.send_message(chat, COMMAND)
                    print(f"Сообщение успешно отправлено в {chat}")
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"Не удалось отправить в {chat}: {e}")
            
            print("Круг завершен. Ждем 30 минут...")
            await asyncio.sleep(1800)  # Пауза 30 минут перед следующим кругом

if __name__ == '__main__':
    asyncio.run(main())
