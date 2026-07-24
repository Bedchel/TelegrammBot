import asyncio
import os
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

# Считываем данные из Secrets
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "").strip()

GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN", "").strip()
REPO = os.getenv("GITHUB_REPOSITORY", "").strip()

MAIN_BOT = '@deltarune_cases_bot'
FARM_NAME = 'Ферма tanatolii'

COMMAND_CASES = "/open DELTARUNE"
COMMAND_FARM = "ферма"

def restart_workflow():
    print("Время работы сессии истекло. Отправляем запрос на перезапуск...")
    if not REPO or not GITHUB_TOKEN:
        print("Ошибка: REPO или MY_GITHUB_TOKEN не заданы.")
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
        raise ValueError("Ошибка: Переменная TELEGRAM_SESSION не найдена!")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        
        print("🔍 Загружаем список всех диалогов для поиска...")
        farm_entity = None
        
        # Поиск чата фермы среди диалогов
        async for dialog in client.iter_dialogs(limit=100):
            if FARM_NAME.lower().strip() in dialog.name.lower().strip():
                farm_entity = dialog.entity
                print(f"✅ НАЙДЕН ЧАТ ФЕРМЫ: '{dialog.name}' (ID: {dialog.id})")

        if not farm_entity:
            print(f"\n❌ ЧАТ '{FARM_NAME}' НЕ НАЙДЕН СРЕДИ 100 ДИАЛОГОВ!")

        # 🌾 1. КЛЕЙМИМ ФЕРМУ ОДИН РАЗ ПРИ СТАРТЕ
        if farm_entity:
            try:
                await client.send_message(farm_entity, COMMAND_FARM)
                print(f"[{FARM_NAME}] 🌾 Отправлена команда: '{COMMAND_FARM}'")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"[{FARM_NAME}] Ошибка при отправке 'ферма': {e}")
        # 📦 3. ЦИКЛ ДЛЯ КЕЙСОВ (10 раз каждые 30.3 минут)
        for circle in range(10): 
            print(f"\n--- Круг {circle + 1}/10 ---")
            
            # Отправка в основной бот
            try:
                await client.send_message(MAIN_BOT, COMMAND_CASES)
                print(f"[{MAIN_BOT}] Отправлено: {COMMAND_CASES}")
            except Exception as e:
                print(f"[{MAIN_BOT}] Ошибка: {e}")
            
            await asyncio.sleep(3)

            # Отправка в чат фермы
            if farm_entity:
                try:
                    await client.send_message(farm_entity, COMMAND_CASES)
                    print(f"[{FARM_NAME}] Отправлено: {COMMAND_CASES}")
                except Exception as e:
                    print(f"[{FARM_NAME}] Ошибка: {e}")
            
            print("Круг завершен. Засыпаем на 30.3 минут...")
            await asyncio.sleep(1820)
        
        # 🔄 4. Перезапуск воркфлоу
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
