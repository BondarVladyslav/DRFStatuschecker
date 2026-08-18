from datetime import timedelta
import logging
import os
from django.utils import timezone
from dotenv import load_dotenv
import requests
from CheckSiteOut.celery import app
from users.models import Token

load_dotenv()


BOT_TOKEN = os.environ.get("BOT_TOKEN")
logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, retry_backoff=10)
def send_report_message(self, telegram_id, text):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": telegram_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
    except:
        logger.log("Lost telegram message for telegram_id %s", telegram_id)
        self.retry()


@app.task
def cleanup_tokens():
    Token.objects.filter(created_at__lt=timezone.now() - timedelta(hours=1)).delete()
