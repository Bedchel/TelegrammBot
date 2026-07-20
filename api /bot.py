import asyncio
from telethon import TelegramClient

api_id = 37587197
api_hash = 'ebe579cce7e826af00b4771f6837908d'
CHATS = ['@deltarune_cases_bot', 'Ферма tanatolii']
COMMAND = "/open DELTARUNE"

async def main():
    # Файл 'my_session' подхватит вашу рабочую сессию
    async with TelegramClient('my_session', api_id, api_hash) as client:
        print("Запуск круга отправки...")
        
        for chat in CHATS:
            try:
                await client.send_message(chat, COMMAND)
                print(f"Сообщение успешно отправлено в {chat}")
                await asyncio.sleep(5) # Короткая пауза между чатами
            except Exception as e:
                print(f"Не удалось отправить в {chat}: {e}")
                
        print("Круг завершен. Выключаемся до следующего запуска по cron.")

if __name__ == '__main__':
    asyncio.run(main())
