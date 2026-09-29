import logging
import os
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from sqlalchemy import select

from database import init_db, async_session
from models import Student, Lesson

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TEACHER_ID = 932503024  # твой Telegram ID

if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN в переменных окружения")

BASE_WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "https://localhost")
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret-webhook-token"
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------- Состояния FSM ----------
class AddLesson(StatesGroup):
    waiting_for_student = State()
    waiting_for_datetime = State()
    waiting_for_title = State()


# ---------- Проверка: преподаватель ли это ----------
def is_teacher(user_id: int) -> bool:
    return user_id == TEACHER_ID


# ---------- Хендлеры ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user

    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.tg_id == user.id)
        )
        student = result.scalar_one_or_none()

        if student is None:
            student = Student(
                tg_id=user.id,
                full_name=user.full_name,
                username=user.username,
            )
            session.add(student)
            await session.commit()
            logging.info(f"Новый ученик: {user.full_name} ({user.id})")

    if is_teacher(user.id):
        await message.answer(
            f"Привет, преподаватель! 👋\n\n"
            f"Доступные команды:\n"
            f"/add_lesson — добавить занятие ученику\n"
            f"/list_lessons — все занятия\n"
            f"/my_lessons — твои занятия"
        )
    else:
        await message.answer(
            f"Привет, {user.full_name}! 👋\n\n"
            f"Команды:\n"
            f"/my_lessons — посмотреть свои занятия\n"
            f"/help — помощь"
        )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — начать\n"
        "/my_lessons — мои занятия\n"
        "/help — эта справка"
    )


@dp.message(Command("my_lessons"))
async def cmd_my_lessons(message: types.Message):
    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.tg_id == message.from       _user.id)
        )
 student = result.scalar_one_or_none()

        if not student:
            await message.answer("Сначала напиши /start")
            return

        lessons_result = await session.execute(
            select(Lesson)
            .where(Lesson.student_id == student.id)
            .order_by(Lesson.datetime_start)
        )
        lessons = lessons_result.scalars().all()

    if not lessons:
        await message.answer("У тебя пока нет занятий.")
        return

    text = "📅 Твои занятия:\n\n"
    for lesson in lessons:
        text += f"• {lesson.datetime_start.strftime('%d.%m.%Y %H:%M')} — {lesson.title}\n"

    await message.answer(text)


# ---------- Команды только для преподавателя ----------
@dp.message(Command("add_lesson"))
async def cmd_add_lesson(message: types.Message, state: FSMContext):
    if not is_teacher(message.from_user.id):
        await message.answer("Эта команда только для преподавателя.")
        return

    await message.answer("Введи Telegram ID ученика (можно узнать у @userinfobot):")
    await state.set_state(AddLesson.waiting_for_student)


@dp.message(AddLesson.waiting_for_student)
async def process_student_id(message: types.Message, state: FSMContext):
    try:
        student_tg_id = int(message.text.strip())
    except ValueError:
        await message.answer("Это не похоже на ID. Введи число.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.tg_id == student_tg_id)
        )
        student = result.scalar_one_or_none()

    if not student:
        await message.answer(
            "Ученик с таким ID не найден в базе.\n"
            "Попроси его написать боту /start, а потом попробуй снова."
        )
        await state.clear()
        return

    await state.update_data(student_id=student.id, student_name=student.full_name)
    await message.answer(
        f"Ученик: {student.full_name}\n\n"
        f"Теперь введи дату и время занятия в формате:\n"
        f"ДД.ММ.ГГГГ ЧЧ:ММ\n"
        f"Например: 15.10.2026 18:30"
    )
    await state.set_state(AddLesson.waiting_for_datetime)


@dp.message(AddLesson.waiting_for_datetime)
async def process_datetime(message: types.Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("Неверный формат. Попробуй ещё раз: 15.10.2026 18:30")
        return

    await state.update_data(datetime_start=dt)
    await message.answer("Введи название занятия (например, «Математика»):")
    await state.set_state(AddLesson.waiting_for_title)


@dp.message(AddLesson.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    data = await state.get_data()
    title = message.text.strip()

    async with async_session() as session:
        lesson = Lesson(
            student_id=data["student_id"],
            datetime_start=data["datetime_start"],
            title=title,
        )
        session.add(lesson)
        await session.commit()

    await message.answer(
        f"✅ Занятие добавлено!\n\n"
        f"Ученик: {data['student_name']}\n"
        f"Дата: {data['datetime_start'].strftime('%d.%m.%Y %H:%M')}\n"
        f"Название: {title}"
    )
    await state.clear()


@dp.message(Command("list_lessons"))
async def cmd_list_lessons(message: types.Message):
    if not is_teacher(message.from_user.id):
        await message.answer("Эта команда только для преподавателя.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(Lesson).order_by(Lesson.datetime_start)
        )
        lessons = result.scalars().all()

    if not lessons:
        await message.answer("Занятий пока нет.")
        return

    text = "📋 Все занятия:\n\n"
    for lesson in lessons:
        text += (
            f"• {lesson.datetime_start.strftime('%d.%m.%Y %H:%M')} — "
            f"{lesson.title} (ID ученика: {lesson.student_id})\n"
        )
    await message.answer(text)


# ---------- Webhook ----------
async def on_startup(bot: Bot) -> None:
    await init_db()
    logging.info("База данных инициализирована")
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    logging.info("Webhook установлен")


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
