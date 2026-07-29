import os
from dotenv import load_dotenv
import requests
load_dotenv()


BOT_TOKEN = os.environ.get('BOT_TOKEN')
def send_report_message(telegram_id, text):
    requests.post(
        f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        json={'chat_id': telegram_id, 'text': text},
        timeout=10,
    )
