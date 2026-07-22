import asyncio
import os
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

# Считываем данные строго из Secrets (без «засвечивания» ключей в коде)
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "").strip()

GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN", "").strip()
REPO = os.getenv("GITHUB_REPOSITORY", "").strip()

# Настройки чатов и команд
MAIN_BOT = '@deltarune_cases_bot'
FARM_BOT = 'Ферма tanatolii'

COMMAND_CASES = "/open DELTARUNE"
COMMAND_FARM = "ферма"

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
        raise ValueError("Ошибка: Переменная TELEGRAM_SESSION не найдена в Secrets!")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        
        # 🌾 1. КЛЕЙМИМ ФЕРМУ ОДИН РАЗ ПРИ СТАРТЕ (раз в ~5 часов)
        try:
            await client.send_message(FARM_BOT, COMMAND_FARM)
            print(f"[{FARM_BOT}] 🌾 Ферма запущена: '{COMMAND_FARM}'")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"[{FARM_BOT}] Ошибка отправки команды фермы: {e}")

        # 📦 2. ЦИКЛ ДЛЯ КЕЙСОВ (каждые 32 минуты, 10 раз)
        for circle in range(10): 
            print(f"\n--- Запуск круга кейсов {circle + 1}/10 ---")
            
            # Отправка в основной бот
            try:
                await client.send_message(MAIN_BOT, COMMAND_CASES)
                print(f"[{MAIN_BOT}] Отправлено: {COMMAND_CASES}")
            except Exception as e:
                print(f"[{MAIN_BOT}] Ошибка: {e}")
            
            await asyncio.sleep(3) # Пауза между сообщениями

            # Отправка во второй чат (Ферма)
            try:
                await client.send_message(FARM_BOT, COMMAND_CASES)
                print(f"[{FARM_BOT}] Отправлено: {COMMAND_CASES}")
            except Exception as e:
                print(f"[{FARM_BOT}] Ошибка: {e}")
            
            print("Круг завершен. Засыпаем на 32 минуты...")
            await asyncio.sleep(1920)
        
        # 🔄 3. Перезапуск всего воркфлоу
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
