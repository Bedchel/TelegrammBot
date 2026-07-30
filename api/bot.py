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
FARM_CHAT_ID = -1002869570983

# Команди
COMMAND_MAIN_CASES = "/open DELTARUNE" # Для основного бота
COMMAND_TOPIC_CASES = "дельтакейс"      # Нова команда для топіка "Дельтакейс"


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

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client

        # 📦 2. ЦИКЛ ДЛЯ КЕЙСІВ (10 разів кожні 31 хвилину)
        for circle in range(10): 
            print(f"\n--- Коло {circle + 1}/10 ---")
            
            # 1. Відправка в основний бот (@deltarune_cases_bot)
            try:
                await client.send_message(MAIN_BOT, COMMAND_MAIN_CASES)
                print(f"[{MAIN_BOT}] Відправлено: {COMMAND_MAIN_CASES}")
            except Exception as e:
                print(f"[{MAIN_BOT}] Помилка: {e}")
            
            await asyncio.sleep(3)

            # 2. Відправка у топік "Дельтакейс" чату Ад tanatolii
            try:
                # Пошук топіка "Дельтакейс" за назвою
                topic_id = None
                async for forum_topic in client.iter_dialogs():
                    pass # Перевірка топіка через пошук повідомлень/структуру
                
                # Знаходимо останнє повідомлення у топіку або надсилаємо з реплаєм
                # Переважно у Телеграм форумах ID топіка — це ID його першого повідомлення.
                # Якщо просто відправити з текстом "дельтакейс", топік підтягнеться автоматично, 
                # якщо знайти його ID.
                
                # Знаходимо останнє повідомлення від когось у топіку "Дельтакейс", щоб відповісти в нього:
                async for message in client.iter_messages(FARM_CHAT_ID, limit=20):
                    if message.reply_to and message.reply_to.forum_topic:
                        # Відправляємо прямо в цей топік
                        await client.send_message(FARM_CHAT_ID, COMMAND_TOPIC_CASES, reply_to=message.reply_to.reply_to_msg_id)
                        print(f"[{FARM_CHAT_ID}] 🎯 Відправлено '{COMMAND_TOPIC_CASES}' у топік Дельтакейс")
                        break
                else:
                    # Якщо топік не визначився через реплай, відправляємо просто в чат
                    await client.send_message(FARM_CHAT_ID, COMMAND_TOPIC_CASES)
                    print(f"[{FARM_CHAT_ID}] Відправлено: {COMMAND_TOPIC_CASES}")

            except Exception as e:
                print(f"[{FARM_CHAT_ID}] Помилка відправки у топік: {e}")
            
            print("Коло завершено. Засинаємо на 31 хвилин...")
            await asyncio.sleep(1860)
        
        # 🔄 3. Перезапуск воркфлоу
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
