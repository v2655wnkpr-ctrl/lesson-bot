import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN в переменных окружения")

logging.basicConfig(level=logging.INFO)

BASE_WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "https://localhost")
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret-webhook-token"
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Привет, {message.from_user.full_name}! 👋\nЯ на webhook!")


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Я пока только учусь. Скоро буду напоминать о занятиях!")


@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Ты написал: {message.text}")


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )


app = web.Application()

webhook_requests_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
    secret_token=WEBHOOK_SECRET,
)
webhook_requests_handler.register(app, path=WEBHOOK_PATH)

setup_application(app, dp, bot=bot)
dp.startup.register(on_startup)


if __name__ == "__main__":
    print(f"Запуск веб-сервера на {WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
