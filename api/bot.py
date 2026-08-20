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
COMMAND_MAIN_CASES = "/open DELTARUNE"
COMMAND_TOPIC_CASES = "дельтакейс"

DEFAULT_SLEEP_TIME = 1830  # Час очікування за замовчуванням (30.5 хв)

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

def parse_cooldown_time(text: str) -> int:
    """Парсить текст повідомлення та повертає час кулдауну в секундах."""
    if not text:
        return 0
    
    # Шукаємо хвилини (м) і секунди (с) у тексті
    minutes_match = re.search(r'(\d+)\s*м', text)
    seconds_match = re.search(r'(\d+)\s*с', text)
    
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0
    
    total_seconds = (minutes * 60) + seconds
    return total_seconds

async def process_chat_and_get_cooldown(client, chat_entity, command, reply_to_topic=None):
    """Шле команду, чекає відповідь, натискає кнопку (якщо є) і витягує час кулдауну."""
    try:
        # Відправляємо команду
        kwargs = {"reply_to": reply_to_topic} if reply_to_topic else {}
        await client.send_message(chat_entity, command, **kwargs)
        print(f"[{chat_entity}] Відправлено команду: '{command}'")
    except Exception as e:
        print(f"[{chat_entity}] Помилка при відправці команди: {e}")
        return 0

    # Чекаємо відповіді від бота (до 20 секунд)
    for _ in range(20):
        await asyncio.sleep(1)
        async for message in client.iter_messages(chat_entity, limit=5, **kwargs):
            if message.text:
                text_lower = message.text.lower()
                
                # 1. Перевіряємо, чи це повідомлення для Mischa
                if "mischa" in text_lower:
                    # Якщо є кнопка підтвердження — тиснемо її та завершуємо (кулдауну немає)
                    if "подтверди открытие кейса" in text_lower and message.buttons:
                        try:
                            await message.click(text="Открыть кейс")
                            print("✅ Кнопку 'Открыть кейс' успішно натиснуто!")
                            return 0
                        except Exception as e:
                            print(f"❌ Помилка при натисканні кнопочки: {e}")
                    
                    # Якщо у повідомленні є фраза про кулдаун — парсимо час
                    if "кулдаун" in text_lower or "попробуй через" in text_lower:
                        cooldown = parse_cooldown_time(message.text)
                        if cooldown > 0:
                            print(f"⏱️ Знайдено кулдаун: {cooldown} секунд ({cooldown // 60}м {cooldown % 60}с)")
                            return cooldown

    return 0

async def main():
    if not SESSION_STRING:
        raise ValueError("Помилка: Перемінна TELEGRAM_SESSION не знайдена!")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:

        # 📦 ЦИКЛ ДЛЯ КЕЙСІВ (10 разів)
        for circle in range(10): 
            print(f"\n--- Коло {circle + 1}/10 ---")
            
            # 1. Відкриваємо/перевіряємо кейс у топіку Дельтакейс
            cooldown_topic = await process_chat_and_get_cooldown(
                client, FARM_CHAT_ID, COMMAND_TOPIC_CASES, reply_to_topic=DELTA_TOPIC_ID
            )
            
            await asyncio.sleep(3)

            # 2. Відкриваємо/перевіряємо кейс в основному боті
            cooldown_main = await process_chat_and_get_cooldown(
                client, MAIN_BOT, COMMAND_MAIN_CASES
            )

            # Вибираємо максимальний знайдений кулдаун серед двох відповідей
            max_cooldown = max(cooldown_topic, cooldown_main)

            if max_cooldown > 0:
                # Додаємо 5 секунд запасу, щоб гарантовано зачекати закінчення кулдауну
                sleep_time = max_cooldown + 5
                print(f"😴 Встановлено таймер сну за кулдауном: {sleep_time} сек ({sleep_time // 60}м {sleep_time % 60}с)")
            else:
                sleep_time = DEFAULT_SLEEP_TIME
                print(f"😴 Кулдаун не виявлено. Засинаємо на стандартний час: {sleep_time} сек ({sleep_time // 60}м)")

            print(f"Коло {circle + 1} завершено.")
            await asyncio.sleep(sleep_time)
        
        # 🔄 Перезапуск воркфлоу
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
