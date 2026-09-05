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

async def send_command_to_bot(client):
    """Шле команду /open DELTARUNE в ЛС боту, натискає кнопку або повертає кулдаун."""
    try:
        sent_msg = await client.send_message(MAIN_BOT, COMMAND_MAIN_CASES, silent=True)
        print(f"[{MAIN_BOT}] Відправлено команду в ЛС: '{COMMAND_MAIN_CASES}'", flush=True)
    except Exception as e:
        print(f"[{MAIN_BOT}] Помилка при відправці команди боту: {e}", flush=True)
        return 0, False

    cooldown_time = 0
    button_clicked = False

    for attempt in range(10):
        await asyncio.sleep(1)
        async for message in client.iter_messages(MAIN_BOT, limit=5, min_id=sent_msg.id):
            if message.text:
                text_lower = message.text.lower()

                # Якщо бот прислав кнопку для відкриття
                if "подтверди открытие кейса" in text_lower and message.buttons:
                    try:
                        for row in message.buttons:
                            for button in row:
                                if "открыть кейс" in button.text.lower():
                                    await button.click()
                                    button_clicked = True
                                    print(f"[{MAIN_BOT}] ✅ Кнопку 'Открыть кейс' успішно натиснуто!", flush=True)
                                    break
                    except Exception as e:
                        print(f"[{MAIN_BOT}] ❌ Помилка натискання кнопки: {e}", flush=True)

                # Якщо бот прислав текст про кулдаун
                if "на кулдауне" in text_lower or "попробуй через" in text_lower:
                    cooldown = parse_cooldown_time(message.text)
                    if cooldown > 0:
                        cooldown_time = cooldown
                        break

        if cooldown_time > 0 or button_clicked:
            break

    return cooldown_time, button_clicked

async def process_full_cycle_in_bot(client):
    """Повний цикл взаємодії з ботом у приватних повідомленнях."""
    # Step 1: Відкриваємо кейс
    cooldown, button_clicked = await send_command_to_bot(client)

    # Step 2: Якщо кейс було відкрито або кулдаун не отримано з 1-ї спроби — питаємо боту ще раз про новий кулдаун
    if button_clicked or cooldown == 0:
        await asyncio.sleep(3)
        print(f"[{MAIN_BOT}] Запитуємо новий кулдаун після відкриття...", flush=True)
        second_cooldown, _ = await send_command_to_bot(client)
        if second_cooldown > 0:
            cooldown = second_cooldown

    return cooldown

async def main():
    if not SESSION_STRING:
        raise ValueError("Помилка: Перемінна TELEGRAM_SESSION не знайдена!")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        for circle in range(10): 
            print(f"\n--- Коло {circle + 1}/10 ---", flush=True)
            
            if not client.is_connected():
                await client.connect()

            # Працюємо виключно в ЛС з ботом
            cooldown = await process_full_cycle_in_bot(client)

            if cooldown > 0:
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
