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
    """Парсить текст повідомлення та повертає точний час кулдауну в секундах без затримок."""
    if not text:
        return 0
    
    minutes_match = re.search(r'(\d+)\s*м', text)
    seconds_match = re.search(r'(\d+)\s*с', text)
    
    if not minutes_match and not seconds_match:
        return 0
    
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0
    
    # Повертаємо чистий час секунда в секунду
    return (minutes * 60) + seconds

async def open_case_in_bot(client):
    """Шле команду боту в ЛС і гарантовано тисне кнопку підтвердження."""
    try:
        sent_msg = await client.send_message(MAIN_BOT, COMMAND_MAIN_CASES, silent=True)
        if sent_msg:
            print(f"[{MAIN_BOT}] Відправлено команду: '{COMMAND_MAIN_CASES}'", flush=True)
            await client.send_read_acknowledge(MAIN_BOT, max_id=sent_msg.id)
    except Exception as e:
        print(f"[{MAIN_BOT}] Помилка при відправці команди: {e}", flush=True)
        return 0

    cooldown_time = 0

    # Чекаємо на відповідь бота (до 15 секунд)
    for attempt in range(15):
        await asyncio.sleep(1)
        async for message in client.iter_messages(MAIN_BOT, limit=5):
            if message.text:
                text_lower = message.text.lower()
                
                # Позначаємо повідомлення від бота прочитаними
                await client.send_read_acknowledge(MAIN_BOT, max_id=message.id)

                # 1. Спроба натиснути кнопку відкриття кейса
                if "подтверди открытие кейса" in text_lower or "открыть кейс" in text_lower:
                    if message.buttons:
                        try:
                            # Шукаємо кнопку перебором усіх елементів
                            for row in message.buttons:
                                for button in row:
                                    await button.click()
                                    print("✅ Кнопку успішно натиснуто через об'єкт button!", flush=True)
                                    await asyncio.sleep(2)
                                    break
                        except Exception as e:
                            print(f"❌ Помилка першого виклику кнопки: {e}", flush=True)
                            try:
                                # Резервний прямий виклик першої кнопки
                                await message.click(0)
                                print("✅ Кнопку натиснуто через message.click(0)!", flush=True)
                            except Exception as err:
                                print(f"❌ Помилка резервного натискання: {err}", flush=True)

                # 2. Отримання точного кулдауну
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
            
            cooldown = await open_case_in_bot(client)

            if cooldown > 0:
                # Додаємо лише 2 секунди запасного часу замість 20
                sleep_time = cooldown + 2
                print(f"⏱️ Отримано кулдаун від бота: {cooldown} сек ({cooldown // 60}м {cooldown % 60}с)", flush=True)
                print(f"😴 Встановлено таймер сну: {sleep_time} сек ({sleep_time // 60}м {sleep_time % 60}с)", flush=True)
            else:
                sleep_time = DEFAULT_SLEEP_TIME
                print(f"😴 Кулдаун не виявлено. Засинаємо на стандартний час: {sleep_time} сек ({sleep_time // 60}м)", flush=True)

            print(f"Коло {circle + 1} завершено.", flush=True)
            await asyncio.sleep(sleep_time)
        
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
