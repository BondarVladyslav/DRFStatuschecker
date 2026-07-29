import os
import sys

from pathlib import Path
import asyncio
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE_DIR)) 
                
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CheckSiteOut.settings")
import django
django.setup()
from dotenv import load_dotenv
load_dotenv()
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from asgiref.sync import sync_to_async
from users.models import Token
BOT_TOKEN = os.environ.get('BOT_TOKEN')
router = Router()

@router.message(CommandStart(deep_link=True))
async def start_with_token(message: Message, command: CommandObject):
    ok = await sync_to_async(link_token)(command.args, message.from_user.id)
    if ok:
        await message.answer("Ready! Go back to site.")
    else:
        await message.answer("Link expired")

@router.message(CommandStart())
async def start_plain(message: Message):
    await message.answer("Please input /start <token>")

def link_token(token, telegram_id):
    updated = Token.objects.filter(
        token=token, telegram_id__isnull=True
    ).update(telegram_id=telegram_id)
    return updated > 0

async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())