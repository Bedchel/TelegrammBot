import asyncio
import re
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
COMMAND_TOPIC_CASES = "дельтакейс"
COMMAND_MAIN_CASES = "/open DELTARUNE"

DEFAULT_SLEEP_TIME = 1830  # Час очікування за замовчуванням (30.5 хв)

def restart_workflow():
    print("Час роботи сесії закінчився. Відправляємо запит на перезапуск...", flush=True)
    if not REPO or not GITHUB_TOKEN:
        print("Помилка: REPO або MY_GITHUB_TOKEN не задані.", flush=True)
        return

    url = f"https://api.github.com/repos/{REPO}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"event_type": "restart_bot"}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 204:
        print("Новий Workflow успішно запущено!", flush=True)
    else:
        print(f"Не вдалося перезапустити: {response.status_code}, {response.text}", flush=True)

def parse_cooldown_time(text: str) -> int:
    """Парсить текст повідомлення та повертає час кулдауну в секундах."""
    if not text:
        return 0
    
    minutes_match = re.search(r'(\d+)\s*м', text)
    seconds_match = re.search(r'(\d+)\s*с', text)
    
    if not minutes_match and not seconds_match:
        return 0
    
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0
    
    # Додаємо 15 секунд затримки тільки якщо час дійсно розпарсився
    total_seconds = (minutes * 60) + seconds + 15
    return total_seconds

async def open_case_in_topic(client):
    """Шле команду в топік чату Танатолій і тисне кнопку 'Открыть кейс', якщо вона є."""
    try:
        kwargs = {"reply_to": DELTA_TOPIC_ID}
        # Шлемо команду з прапором silent окремо від kwargs
        sent_msg = await client.send_message(FARM_CHAT_ID, COMMAND_TOPIC_CASES, silent=True, **kwargs)
        print(f"[{FARM_CHAT_ID}] Відправлено команду: '{COMMAND_TOPIC_CASES}'", flush=True)
        
        if sent_msg:
            await client.send_read_acknowledge(FARM_CHAT_ID, max_id=sent_msg.id, top_msg_id=DELTA_TOPIC_ID)
            
    except Exception as e:
        print(f"[{FARM_CHAT_ID}] Помилка при відправці команди: {e}", flush=True)
        return

    # Чекаємо відповіді у топіку до 15 секунд, щоб натиснути кнопку
    for _ in range(15):
        await asyncio.sleep(1)
        async for message in client.iter_messages(FARM_CHAT_ID, limit=5, **kwargs):
            if message.text:
                text_lower = message.text.lower()
                if "mischa" in text_lower and "подтверди открытие кейса" in text_lower and message.buttons:
                    try:
                        await message.click(text="Открыть кейс")
                        print("✅ Кнопку 'Открыть кейс' успішно натиснуто в чаті Танатолій!", flush=True)
                        
                        # Позначаємо прочитаними поточні повідомлення
                        await client.send_read_acknowledge(FARM_CHAT_ID, max_id=message.id, top_msg_id=DELTA_TOPIC_ID)
                        
                        # Коротке очікування фінального повідомлення від бота і його прочитання
                        await asyncio.sleep(2)
                        async for last_msg in client.iter_messages(FARM_CHAT_ID, limit=2, **kwargs):
                            await client.send_read_acknowledge(FARM_CHAT_ID, max_id=last_msg.id, top_msg_id=DELTA_TOPIC_ID)
                        return
                    except Exception as e:
                        print(f"❌ Помилка при натисканні кнопки: {e}", flush=True)
                        return

async def get_cooldown_from_bot(client):
    """Шле команду боту в приватні повідомлення, щоб дізнатися кулдаун."""
    try:
        sent_msg = await client.send_message(MAIN_BOT, COMMAND_MAIN_CASES, silent=True)
        print(f"[{MAIN_BOT}] Відправлено команду перевірки кулдауну: '{COMMAND_MAIN_CASES}'", flush=True)
    except Exception as e:
        print(f"[{MAIN_BOT}] Помилка при відправці команди боту: {e}", flush=True)
        return 0

    # Чекаємо відповіді в ЛС бота (до 15 секунд)
    for _ in range(15):
        await asyncio.sleep(1)
        async for message in client.iter_messages(MAIN_BOT, limit=5):
            if message.text:
                text_lower = message.text.lower()
                if "mischa" in text_lower or "кулдаун" in text_lower or "попробуй через" in text_lower:
                    cooldown = parse_cooldown_time(message.text)
                    
                    # Позначаємо всі повідомлення від бота прочитаними
                    await client.send_read_acknowledge(MAIN_BOT, max_id=message.id)
                    
                    if cooldown > 0:
                        print(f"⏱️ Отримано кулдаун від бота: {cooldown} секунд ({cooldown // 60}м {cooldown % 60}с)", flush=True)
                        return cooldown

    return 0

async def main():
    if not SESSION_STRING:
        raise ValueError("Помилка: Перемінна TELEGRAM_SESSION не знайдена!")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:

        # 📦 ЦИКЛ ДЛЯ КЕЙСІВ (10 разів)
        for circle in range(10): 
            print(f"\n--- Коло {circle + 1}/10 ---", flush=True)
            
            # 1. Відкриваємо кейс у чаті Танатолій (і тиснемо кнопку)
            await open_case_in_topic(client)
            
            # Невелика пауза між діями
            await asyncio.sleep(3)

            # 2. Отримуємо точний кулдаун через ЛС з ботом
            cooldown = await get_cooldown_from_bot(client)

            if cooldown > 0:
                sleep_time = cooldown + 5
                print(f"😴 Встановлено таймер сну за кулдауном: {sleep_time} сек ({sleep_time // 60}м {sleep_time % 60}с)", flush=True)
            else:
                sleep_time = DEFAULT_SLEEP_TIME
                print(f"😴 Кулдаун не виявлено. Засинаємо на стандартний час: {sleep_time} сек ({sleep_time // 60}м)", flush=True)

            print(f"Коло {circle + 1} завершено.", flush=True)
            await asyncio.sleep(sleep_time)
        
        # 🔄 Перезапуск воркфлоу
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
