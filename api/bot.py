import asyncio
import os
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

# Зчитуємо дані з Secrets
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "").strip()

GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN", "").strip()
REPO = os.getenv("GITHUB_REPOSITORY", "").strip()

MAIN_BOT = '@deltarune_cases_bot'
FARM_CHAT_ID = '@tanatoliiss'

# 🎯 Точний ID топіка "Дельтакейс"
DELTA_TOPIC_ID = 132244 

# Команди
COMMAND_MAIN_CASES = "/open DELTARUNE"
COMMAND_TOPIC_CASES = "дельтакейс"

def restart_workflow():
    print("Час роботи сесії закінчився. Відправляємо запит на перезапуск...")
    if not REPO or not GITHUB_TOKEN:
        print("Помилка: REPO або MY_GITHUB_TOKEN не задані.")
        return

    url = f"https://api.github.com/repos/{REPO}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"event_type": "restart_bot"}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 204:
        print("Новий Workflow успішно запущено!")
    else:
        print(f"Не вдалося перезапустити: {response.status_code}, {response.text}")

async def main():
    if not SESSION_STRING:
        raise ValueError("Помилка: Перемінна TELEGRAM_SESSION не знайдена!")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:

        # 📦 ЦИКЛ ДЛЯ КЕЙСІВ (10 разів кожні 31 хвилину)
        for circle in range(10): 
            print(f"\n--- Коло {circle + 1}/10 ---")
            
            # 1. Сначала отправка Танатолию (в топик Дельтакейс)
            try:
                await client.send_message(
                    FARM_CHAT_ID, 
                    COMMAND_TOPIC_CASES, 
                    reply_to=DELTA_TOPIC_ID  # Шле строго у гілку Дельтакейс
                )
                print(f"[{FARM_CHAT_ID}] 🎯 Відправлено '{COMMAND_TOPIC_CASES}' у топік Дельтакейс (ID: {DELTA_TOPIC_ID})")
            except Exception as e:
                print(f"[{FARM_CHAT_ID}] Помилка відправки у топік: {e}")
            
            # Пауза 3 секунды между сообщениями
            await asyncio.sleep(3)

            # 2. Затем отправка в основной бот (@deltarune_cases_bot)
            try:
                await client.send_message(MAIN_BOT, COMMAND_MAIN_CASES)
                print(f"[{MAIN_BOT}] Відправлено: {COMMAND_MAIN_CASES}")
            except Exception as e:
                print(f"[{MAIN_BOT}] Помилка: {e}")
            
            print("Коло завершено. Засинаємо на 31 хвилин...")
            await asyncio.sleep(1860)
        
        # 🔄 Перезапуск воркфлоу
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
