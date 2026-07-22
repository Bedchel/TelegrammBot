import asyncio
import os
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

# Считываем конфиденциальные данные из переменных окружения
API_ID = int(os.getenv("TELEGRAM_API_ID", "37587197"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "ebe579cce7e826af00b4771f6837908d")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "").strip()

GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN", "").strip()
REPO = os.getenv("GITHUB_REPOSITORY", "").strip()

CHATS = ['@deltarune_cases_bot', 'Ферма tanatolii']
COMMAND = "/open DELTARUNE"

def restart_workflow():
    print("Время работы текущей сессии истекло. Отправляем запрос на перезапуск...")
    if not REPO or not GITHUB_TOKEN:
        print("Ошибка: REPO или MY_GITHUB_TOKEN не заданы в окружении.")
        return

    url = f"https://api.github.com/repos/{REPO}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"event_type": "restart_bot"}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 204:
        print("Новый Workflow успешно запущен!")
    else:
        print(f"Не удалось перезапустить: {response.status_code}, {response.text}")

async def main():
    if not SESSION_STRING:
        raise ValueError("Ошибка: Переменная TELEGRAM_SESSION не передана!")

    # Авторизуемся по безопасной строке из Secrets
    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        for circle in range(10): 
            print(f"Запуск круга отправки {circle + 1}/10...")
            for chat in CHATS:
                try:
                    await client.send_message(chat, COMMAND)
                    print(f"Сообщение успешно отправлено в {chat}")
                    await asyncio.sleep(3)
                except Exception as e:
                    print(f"Не удалось отправить в {chat}: {e}")
            
            print("Круг завершен. Засыпаем на 32 минуты...")
            await asyncio.sleep(1920)
        
        # Перезапуск после 10 циклов
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
