from datetime import timedelta
import os
from django.utils import timezone
from dotenv import load_dotenv
import requests
from CheckSiteOut.celery import app
from users.models import Token

load_dotenv()


BOT_TOKEN = os.environ.get("BOT_TOKEN")


@app.task(bind=True, max_retries=3, retry_backoff=10)
def send_report_message(self, telegram_id, text):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": telegram_id, "text": text},
        timeout=10,
    )
    response.raise_for_status()


@app.task
def cleanup_tokens():
    Token.objects.filter(created_at__lt=timezone.now() - timedelta(hours=1)).delete()
