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

# Команда для відкриття кейса та перевірки кулдауну
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
    
    total_seconds = (minutes * 60) + seconds + 15
    return total_seconds

async def open_case_in_bot(client):
    """Шле команду відкриття боту в ЛС і тисне кнопку 'Открыть кейс' (якщо вона з'являється)."""
    sent_msg_id = None
    try:
        sent_msg = await client.send_message(MAIN_BOT, COMMAND_MAIN_CASES, silent=True)
        if sent_msg:
            sent_msg_id = sent_msg.id
            print(f"[{MAIN_BOT}] Відправлено команду: '{COMMAND_MAIN_CASES}'", flush=True)
            await client.send_read_acknowledge(MAIN_BOT, max_id=sent_msg_id)
    except Exception as e:
        print(f"[{MAIN_BOT}] Помилка при відправці команди: {e}", flush=True)
        return 0

    cooldown_time = 0

    # Чекаємо відповіді у приватних повідомленнях
    for attempt in range(15):
        await asyncio.sleep(1)
        async for message in client.iter_messages(MAIN_BOT, limit=5):
            if message.text:
                text_lower = message.text.lower()
                
                # Позначаємо прочитаними повідомлення від бота
                await client.send_read_acknowledge(MAIN_BOT, max_id=message.id)

                # 1. Якщо бот видає кнопку підтвердження
                if "подтверди открытие кейса" in text_lower and message.buttons:
                    try:
                        await message.click(0)
                        print("✅ Кнопку 'Открыть кейс' натиснуто у ЛС бота!", flush=True)
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"❌ Помилка при натисканні кнопки: {e}", flush=True)

                # 2. Якщо бот повертає інформацію про кулдаун
                if "mischa" in text_lower or "кулдаун" in text_lower or "попробуй через" in text_lower:
                    cooldown = parse_cooldown_time(message.text)
                    if cooldown > 0:
                        cooldown_time = cooldown

        if cooldown_time > 0:
            break

    return cooldown_time

async def main():
    if not SESSION_STRING:
        raise ValueError("Помилка: Перемінна TELEGRAM_SESSION не знайдена!")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        for circle in range(10): 
            print(f"\n--- Коло {circle + 1}/10 ---", flush=True)
            
            # Відкриваємо кейс і одразу отримуємо кулдаун у приватних повідомленнях бота
            cooldown = await open_case_in_bot(client)

            if cooldown > 0:
                sleep_time = cooldown + 5
                print(f"⏱️ Отримано кулдаун від бота: {cooldown} сек.", flush=True)
                print(f"😴 Встановлено таймер сну: {sleep_time} сек ({sleep_time // 60}м {sleep_time % 60}с)", flush=True)
            else:
                sleep_time = DEFAULT_SLEEP_TIME
                print(f"😴 Кулдаун не виявлено. Засинаємо на стандартний час: {sleep_time} сек ({sleep_time // 60}м)", flush=True)

            print(f"Коло {circle + 1} завершено.", flush=True)
            await asyncio.sleep(sleep_time)
        
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
