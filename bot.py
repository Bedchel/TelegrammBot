import asyncio
import random
from telethon import TelegramClient

# Ваши данные из my.telegram.org
api_id = 37587197
api_hash = 'ebe579cce7e826af00b4771f6837908d'
# Список чатов (username или ID)
CHATS = ['@deltarune_cases_bot', 'Ферма tanatolii']
COMMAND = "/open DELTARUNE"


async def main():
    async with TelegramClient('my_session', api_id, api_hash) as client:
        print("Юзербот запущен и начинает работу...")

        while True:
            for chat in CHATS:
                try:
                    await client.send_message(chat, COMMAND)
                    print(f"Сообщение успешно отправлено в {chat}")
                    # Короткая пауза между отправкой в разные чаты (например, 5 секунд)
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"Не удалось отправить в {chat}: {e}")

            # Генерируем случайное время ожидания от 15.5 до 17.5 минут.
            sleep_time = random.randint(1100, 1250)

            print(f"Ждем {sleep_time // 60} мин. и {sleep_time % 60} сек. перед следующим кругом...")
            await asyncio.sleep(sleep_time)


if __name__ == '__main__':
    asyncio.run(main())
