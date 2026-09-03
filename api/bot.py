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
    """Парсить текст повідомлення та повертає час кулдауну в секундах без затримок."""
    if not text:
        return 0
    
    minutes_match = re.search(r'(\d+)\s*м', text)
    seconds_match = re.search(r'(\d+)\s*с', text)
    
    if not minutes_match and not seconds_match:
        return 0
    
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0
    
    return (minutes * 60) + seconds

async def open_case_in_topic(client):
    """Шле команду в топік Танатолія і тисне кнопку відкриття."""
    sent_msg_id = None
    try:
        sent_msg = await client.send_message(
            FARM_CHAT_ID, 
            COMMAND_TOPIC_CASES, 
            reply_to=DELTA_TOPIC_ID, 
            silent=True
        )
        if sent_msg:
            sent_msg_id = sent_msg.id
            print(f"[{FARM_CHAT_ID}] Відправлено команду у топік: '{COMMAND_TOPIC_CASES}'", flush=True)
            await client.send_read_acknowledge(FARM_CHAT_ID, max_id=sent_msg_id, top_msg_id=DELTA_TOPIC_ID)
    except Exception as e:
        print(f"[{FARM_CHAT_ID}] Помилка при відправці команди: {e}", flush=True)
        return

    # Чекаємо повідомлення з кнопкою у топіку
    for attempt in range(15):
        await asyncio.sleep(1)
        async for message in client.iter_messages(FARM_CHAT_ID, limit=10):
            # Перевіряємо, чи стосується повідомлення нашого топіка/відповіді
            is_our_topic = (
                (message.reply_to and message.reply_to.reply_to_msg_id == DELTA_TOPIC_ID) or
                (message.reply_to and message.reply_to.reply_to_msg_id == sent_msg_id)
            )
            
            if is_our_topic or (message.text and "подтверди открытие кейса" in message.text.lower()):
                if message.buttons:
                    try:
                        # Шукаємо потрібну Inline-кнопку і тиснемо
                        for row in message.buttons:
                            for button in row:
                                await button.click()
                                print("✅ Кнопку успішно натиснуто в топіку чату!", flush=True)
                                await client.send_read_acknowledge(FARM_CHAT_ID, max_id=message.id, top_msg_id=DELTA_TOPIC_ID)
                                return
                    except Exception as e:
                        print(f"❌ Помилка натискання кнопкою: {e}", flush=True)
                        try:
                            await message.click(0)
                            print("✅ Кнопку натиснуто через message.click(0)!", flush=True)
                            await client.send_read_acknowledge(FARM_CHAT_ID, max_id=message.id, top_msg_id=DELTA_TOPIC_ID)
                            return
                        except Exception as err:
                            print(f"❌ Помилка резервного натискання: {err}", flush=True)

async def get_cooldown_from_bot(client):
    """Шле команду перевірки в приватні повідомлення бота, щоб отримати кулдаун."""
    try:
        sent_msg = await client.send_message(MAIN_BOT, COMMAND_MAIN_CASES, silent=True)
        if sent_msg:
            print(f"[{MAIN_BOT}] Відправлено запит кулдауну в ЛС: '{COMMAND_MAIN_CASES}'", flush=True)
            await client.send_read_acknowledge(MAIN_BOT, max_id=sent_msg.id)
    except Exception as e:
        print(f"[{MAIN_BOT}] Помилка при відправці запиту боту: {e}", flush=True)
        return 0

    cooldown_time = 0

    for attempt in range(15):
        await asyncio.sleep(1)
        async for message in client.iter_messages(MAIN_BOT, limit=5):
            if message.text:
                text_lower = message.text.lower()
                await client.send_read_acknowledge(MAIN_BOT, max_id=message.id)

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
            
            # 1. Відкриваємо кейс та підтверджуємо в чаті Танатолій
            await open_case_in_topic(client)
            await asyncio.sleep(3)

            # 2. Перевіряємо точний кулдаун у приватних повідомленнях бота
            cooldown = await get_cooldown_from_bot(client)

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
