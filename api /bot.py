import asyncio
from http.server import BaseHTTPRequestHandler
from telethon import TelegramClient

api_id = 37587197
api_hash = 'ebe579cce7e826af00b4771f6837908d'
CHATS = ['@deltarune_cases_bot']
COMMAND = "/open DELTARUNE"

async def run_bot():
    # Ищем сессию в той же папке api/
    async with TelegramClient('api/my_session', api_id, api_hash) as client:
        print("Запуск круга отправки...")
        for chat in CHATS:
            try:
                await client.send_message(chat, COMMAND)
                print(f"Сообщение успешно отправлено в {chat}")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"Не удалось отправить в {chat}: {e}")

# Класс, который Vercel использует для обработки вызова
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Запускаем отправку сообщений в Telegram
        asyncio.run(run_bot())
        
        # Отвечаем серверу Vercel, что всё прошло успешно
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Бот успешно отработал круг!'.encode('utf-8'))
