import asyncio
import os
from telethon import TelegramClient

api_id = 37587197
api_hash = 'ebe579cce7e826af00b4771f6837908d'

# Оба чата: первый бот и твоя ферма
CHATS = ['@deltarune_cases_bot']
COMMAND = "/open DELTARUNE"

async def main():
    # Автоматически находим, где лежит файл сессии, чтобы не привязываться к api/
    session_path = 'my_session'
    if os.path.exists('api/my_session.session'):
        session_path = 'api/my_session'

    async with TelegramClient(session_path, api_id, api_hash) as client:
        while True: # Бесконечный цикл работы
            print("Запуск круга отправки...")
            for chat in CHATS:
                try:
                    await client.send_message(chat, COMMAND)
                    print(f"Сообщение успешно отправлено в {chat}")
                    await asyncio.sleep(3) # Небольшая пауза между отправками
                except Exception as e:
                    print(f"Не удалось отправить в {chat}: {e}")
            
            print("Круг завершен. Засыпаем на 30 минут...")
            await asyncio.sleep(1) # Спим ровно 30 минут (1800 секунд)

if __name__ == '__main__':
    asyncio.run(main())
