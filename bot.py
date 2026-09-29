import logging
import os
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from sqlalchemy import select

from database import init_db, async_session
from models import Student, Lesson


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TEACHER_ID = 932503024

if not BOT_TOKEN:
    msg = "Не найден BOT_TOKEN"
    raise ValueError(msg)

logging.basicConfig(level=logging.INFO)

BASE_WEBHOOK_URL = os.getenv(
    "RENDER_EXTERNAL_URL",
    "https://localhost",
)
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret-token"
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class AddLesson(StatesGroup):
    student = State()
    dt = State()
    title = State()


def is_teacher(uid: int) -> bool:
    return uid == TEACHER_ID


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    uid = user.id

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == uid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

        if student is None:
            student = Student(
                tg_id=uid,
                full_name=user.full_name,
                username=user.username,
            )
            session.add(student)
            await session.commit()

    if is_teacher(uid):
        text = (
            "Привет, преподаватель!\n\n"
            "Команды:\n"
            "/add_lesson — добавить занятие\n"
            "/list_lessons — все занятия\n"
            "/my_lessons — мои занятия"
        )
    else:
        text = (
            f"Привет, {user.full_name}!\n\n"
            "Команды:\n"
            "/my_lessons — мои занятия\n"
            "/help — помощь"
        )

    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "Доступные команды:\n"
        "/start — начать\n"
        "/my_lessons — мои занятия\n"
        "/help — справка"
    )
    await message.answer(text)


@dp.message(Command("my_lessons"))
async def cmd_my_lessons(message: types.Message):
    uid = message.from_user.id

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == uid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

        if not student:
            await message.answer("Сначала напиши /start")
            return

        q2 = (
            select(Lesson)
            .where(Lesson.student_id == student.id)
            .order_by(Lesson.datetime_start)
        )
        result2 = await session.execute(q2)
        lessons = result2.scalars().all()

    if not lessons:
        await message.answer("У тебя пока нет занятий.")
        return

    lines = ["Твои занятия:\n"]
    for lesson in lessons:
        dt = lesson.datetime_start
        line = f"• {dt.strftime('%d.%m.%Y %H:%M')}"
        line += f" — {lesson.title}"
        lines.append(line)

    await message.answer("\n".join(lines))


@dp.message(Command("add_lesson"))
async def cmd_add_lesson(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    if not is_teacher(uid):
        await message.answer("Только для преподавателя.")
        return

    await message.answer("Введи Telegram ID ученика:")
    await state.set_state(AddLesson.student)


@dp.message(AddLesson.student)
async def process_student(message: types.Message, state: FSMContext):
    try:
        sid = int(message.text.strip())
    except ValueError:
        await message.answer("Это не число. Введи ID.")
        return

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == sid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

    if not student:
        await message.answer(
            "Ученик не найден. Пусть напишет /start."
        )
        await state.clear()
        return

    await state.update_data(
        student_id=student.id,
        student_name=student.full_name,
    )
    text = (
        f"Ученик: {student.full_name}\n\n"
        "Введи дату и время:\n"
        "ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Например: 15.10.2026 18:30"
    )
    await message.answer(text)
    await state.set_state(AddLesson.dt)


@dp.message(AddLesson.dt)
async def process_dt(message: types.Message, state: FSMContext):
    try:
        dt = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y %H:%M",
        )
    except ValueError:
        await message.answer(
            "Неверный формат. Пример: 15.10.2026 18:30"
        )
        return

    await state.update_data(dt=dt)
    await message.answer("Введи название занятия:")
    await state.set_state(AddLesson.title)


@dp.message(AddLesson.title)
async def process_title(
    message: types.Message,
    state: FSMContext,
):
    data = await state.get_data()
    title = message.text.strip()

    async with async_session() as session:
        lesson = Lesson(
            student_id=data["student_id"],
            datetime_start=data["dt"],
            title=title,
        )
        session.add(lesson)
        await session.commit()

    dt = data["dt"]
    text = (
        "Занятие добавлено!\n\n"
        f"Ученик: {data['student_name']}\n"
        f"Дата: {dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"Название: {title}"
    )
    await message.answer(text)
    await state.clear()


@dp.message(Command("list_lessons"))
async def cmd_list_lessons(message: types.Message):
    uid = message.from_user.id
    if not is_teacher(uid):
        await message.answer("Только для преподавателя.")
        return

    async with async_session() as session:
        q = select(Lesson).order_by(Lesson.datetime_start)
        result = await session.execute(q)
        lessons = result.scalars().all()

    if not lessons:
        await message.answer("Занятий пока нет.")
        return

    lines = ["Все занятия:\n"]
    for lesson in lessons:
        dt = lesson.datetime_start
        line = f"• {dt.strftime('%d.%m.%Y %H:%M')}"
        line += f" — {lesson.title}"
        line += f" (id: {lesson.student_id})"
        lines.append(line)

    await message.answer("\n".join(lines))


async def on_startup(bot: Bot) -> None:
    await init_db()
    logging.info("БД готова")
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
    )
    logging.info("Webhook установлен")


app = web.Application()

handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
    secret_token=WEBHOOK_SECRET,
)
handler.register(app, path=WEBHOOK_PATH)

setup_application(app, dp, bot=bot)
dp.startup.register(on_startup)


if __name__ == "__main__":
    print("Сервер запущен")
    web.run_app(
        app,
        host=WEB_SERVER_HOST,
        port=WEB_SERVER_PORT,
    )
