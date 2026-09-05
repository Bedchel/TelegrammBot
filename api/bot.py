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
    """Парсить текст типу 'Попробуй через 13м 16с' або 'через 59с'."""
    if not text:
        return 0
    
    minutes_match = re.search(r'(\d+)\s*м', text)
    seconds_match = re.search(r'(\d+)\s*с', text)
    
    if not minutes_match and not seconds_match:
        return 0
    
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0
    
    return (minutes * 60) + seconds

async def interact_with_main_bot(client):
    """Шле '/open DELTARUNE' у ЛС боту, тисне кнопку при наявності та зчитує кулдаун."""
    try:
        sent_msg = await client.send_message(MAIN_BOT, COMMAND_MAIN_CASES, silent=True)
        print(f"[{MAIN_BOT}] Відправлено команду в ЛС: '{COMMAND_MAIN_CASES}'", flush=True)
    except Exception as e:
        print(f"[{MAIN_BOT}] Помилка при відправці команди боту: {e}", flush=True)
        return 0

    cooldown_time = 0

    # Чекаємо відповіді від бота в ЛС
    for attempt in range(12):
        await asyncio.sleep(1)
        async for message in client.iter_messages(MAIN_BOT, limit=5, min_id=sent_msg.id):
            if message.text:
                text_lower = message.text.lower()

                # Якщо бот прислав підтвердження з кнопкою
                if "подтверди открытие кейса" in text_lower and message.buttons:
                    try:
                        for row in message.buttons:
                            for button in row:
                                if "открыть кейс" in button.text.lower():
                                    await button.click()
                                    print(f"[{MAIN_BOT}] ✅ Кнопку 'Открыть кейс' успішно натиснуто!", flush=True)
                                    break
                    except Exception as e:
                        print(f"[{MAIN_BOT}] ❌ Помилка натискання кнопки: {e}", flush=True)

                # Якщо бот відповідає про кулдаун
                if "на кулдауне" in text_lower or "попробуй через" in text_lower:
                    cooldown = parse_cooldown_time(message.text)
                    if cooldown > 0:
                        cooldown_time = cooldown
                        break

        if cooldown_time > 0:
            break

    return cooldown_time

async def main():
    if not SESSION_STRING:
        raise ValueError("Помилка: Перемінна TELEGRAM_SESSION не знайдена!")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        for circle in range(10): 
            print(f"\n--- Коло {circle + 1}/10 ---", flush=True)
            
            if not client.is_connected():
                await client.connect()

            # Взаємодіємо з головним ботом у ЛС
            cooldown = await interact_with_main_bot(client)

            if cooldown > 0:
                sleep_time = cooldown + 2
                print(f"⏱️ Отримано кулдаун від бота: {cooldown} сек ({cooldown // 60}м {cooldown % 60}с)", flush=True)
                print(f"😴 Встановлено таймер сну: {sleep_time} сек ({sleep_time // 60}м {sleep_time % 60}с)", flush=True)
            else:
                sleep_time = DEFAULT_SLEEP_TIME
                print(f"😴 Кулдаун не виявлено (або кейс щойно відкрито). Засинаємо на стандартний час: {sleep_time} сек ({sleep_time // 60}м)", flush=True)

            print(f"Коло {circle + 1} завершено.", flush=True)
            await asyncio.sleep(sleep_time)
        
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
