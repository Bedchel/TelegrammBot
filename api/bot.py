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
FARM_CHAT_ID = '@tanatoliiss'

# 🎯 Точний ID топіка "Дельтакейс"
DELTA_TOPIC_ID = 132244 

# Команди
COMMAND_MAIN_CASES = "/open DELTARUNE"
COMMAND_TOPIC_CASES = "дельтакейс"

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

async def click_confirmation_button(client, chat_entity, reply_to_topic=None):
    """Чекає на повідомлення з кнопкою підтвердження та натискає її."""
    print("⏳ Чекаємо на повідомлення з кнопкою підтвердження для Mischa...")
    
    # Очікуємо до 30 секунд (30 спроб по 1 секунді)
    for _ in range(30):  
        await asyncio.sleep(1)
        
        # Якщо відправляли у топік, шукаємо відповідь саме у ньому
        kwargs = {"reply_to": reply_to_topic} if reply_to_topic else {}
        
        async for message in client.iter_messages(chat_entity, limit=5, **kwargs):
            if message.text:
                text_lower = message.text.lower()
                # Перевіряємо, що повідомлення адресоване саме тебе і містить ключову фразу
                if "mischa" in text_lower and "подтверди открытие кейса" in text_lower:
                    if message.buttons:
                        try:
                            # Шукаємо кнопку з текстом "Открыть кейс" і тиснемо
                            await message.click(text="Открыть кейс")
                            print("✅ Кнопку 'Открыть кейс' успішно натиснуто!")
                            return True
                        except Exception as e:
                            print(f"❌ Помилка при натисканні на кнопку: {e}")
                            return False
                            
    print("⚠️ Повідомлення з кнопкою підтвердження не було знайдено протягом 30 сек.")
    return False

async def main():
    if not SESSION_STRING:
        raise ValueError("Помилка: Перемінна TELEGRAM_SESSION не знайдена!")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:

        # 📦 ЦИКЛ ДЛЯ КЕЙСІВ (10 разів кожні 15.5 хвилин)
        for circle in range(10): 
            print(f"\n--- Коло {circle + 1}/10 ---")
            
            # 1. Відправка Танатолію (в топік Дельтакейс)
            try:
                await client.send_message(
                    FARM_CHAT_ID, 
                    COMMAND_TOPIC_CASES, 
                    reply_to=DELTA_TOPIC_ID  # Шле строго у гілку Дельтакейс
                )
                print(f"[{FARM_CHAT_ID}] 🎯 Відправлено '{COMMAND_TOPIC_CASES}' у топік Дельтакейс")
                
                # Перевіряємо та тиснемо кнопку в топіку Танатолія
                await click_confirmation_button(client, FARM_CHAT_ID, reply_to_topic=DELTA_TOPIC_ID)

            except Exception as e:
                print(f"[{FARM_CHAT_ID}] Помилка відправки у топік: {e}")
            
            # Пауза 3 секунди між відправками
            await asyncio.sleep(3)

            # 2. Відправка в основний бот (@deltarune_cases_bot)
            try:
                await client.send_message(MAIN_BOT, COMMAND_MAIN_CASES)
                print(f"[{MAIN_BOT}] Відправлено: {COMMAND_MAIN_CASES}")
                
                # Перевіряємо та тиснемо кнопку в основному боті (якщо вона там є)
                await click_confirmation_button(client, MAIN_BOT)

            except Exception as e:
                print(f"[{MAIN_BOT}] Помилка: {e}")
            
            print("Коло завершено. Засинаємо на 15.5 хвилин...")
            await asyncio.sleep(1260)  # 15.5 хвилин = 930 секунд
        
        # 🔄 Перезапуск воркфлоу
        restart_workflow()

if __name__ == '__main__':
    asyncio.run(main())
