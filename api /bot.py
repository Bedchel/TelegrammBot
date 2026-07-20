import asyncio
from http.server import BaseHTTPRequestHandler
from telethon import TelegramClient

api_id = 37587197
api_hash = 'ebe579cce7e826af00b4771f6837908d'
CHATS = ['@deltarune_cases_bot']  # Точный юзернейм с вашего первого скриншота!
COMMAND = "/open DELTARUNE"

async def run_bot():
    # Указываем путь к сессии, которая лежит в той же папке api
    async with TelegramClient('api/my_session', api_id, api_hash) as client:
        print("Запуск круга отправки...")
        for chat in CHATS:
            try:
                await client.send_message(chat, COMMAND)
                print(f"Сообщение успешно отправлено в {chat}")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"Не удалось отправить в {chat}: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Выполняем отправку сообщений
        asyncio.run(run_bot())
        
        # Отвечаем Vercel, что всё прошло успешно
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write('Бот успешно отработал круг!'.encode('utf-8'))
