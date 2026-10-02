import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from dotenv import load_dotenv
from sqlalchemy import select

from database import init_db, async_session
from models import Student, Lesson
from scheduler import start_scheduler, now_msk


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


def hours_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="За 1 час", callback_data="h:1"
            ),
            InlineKeyboardButton(
                text="За 3 часа", callback_data="h:3"
            ),
        ],
        [
            InlineKeyboardButton(
                text="За 1 день", callback_data="h:24"
            ),
            InlineKeyboardButton(
                text="За 2 дня", callback_data="h:48"
            ),
        ],
        [
            InlineKeyboardButton(
                text="За неделю", callback_data="h:168"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def hours_text(hours: int) -> str:
    if hours == 1:
        return "за 1 час"
    if hours == 24:
        return "за 1 день"
    if hours == 48:
        return "за 2 дня"
    if hours == 168:
        return "за неделю"
    return f"за {hours} ч."


def students_keyboard(students) -> InlineKeyboardMarkup:
    """Кнопки с учениками."""
    buttons = []
    for s in students:
        name = s.full_name
        if len(name) > 30:
            name = name[:30] + "..."
        buttons.append([
            InlineKeyboardButton(
                text=name,
                callback_data=f"st:{s.id}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lessons_keyboard(lessons, students_map):
    """Кнопки с занятиями для переноса (на будущее)."""
    buttons = []
    for lesson in lessons:
        name = students_map.get(
            lesson.student_id, "?"
        )
        dt = lesson.datetime_start
        label = (
            f"{dt.strftime('%d.%m %H:%M')} — "
            f"{name}"
        )
        buttons.append([
            InlineKeyboardButton(
                text=label,
                callback_data=f"ls:{lesson.id}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
            "/my_lessons — мои занятия\n"
            "/stats — статистика"
        )
    else:
        text = (
            f"Привет, {user.full_name}!\n\n"
            "Команды:\n"
            "/my_lessons — мои занятия\n"
            "/settings — напоминания\n"
            "/help — помощь"
        )

    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "Доступные команды:\n"
        "/start — начать\n"
        "/my_lessons — мои занятия\n"
        "/settings — напоминания\n"
        "/help — справка"
    )
    await message.answer(text)


@dp.message(Command("settings"))
async def cmd_settings(message: types.Message):
    uid = message.from_user.id

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == uid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

    if not student:
        await message.answer("Сначала напиши /start")
        return

    hours = student.custom_hours_before or 2
    text = (
        f"Сейчас напоминаю {hours_text(hours)}.\n\n"
        "Выбери, за сколько напоминать:"
    )
    await message.answer(
        text, reply_markup=hours_keyboard()
    )


@dp.callback_query(lambda c: c.data.startswith("h:"))
async def process_hours(callback: CallbackQuery):
    hours = int(callback.data.split(":")[1])
    uid = callback.from_user.id

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == uid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

        if student:
            student.custom_hours_before = hours
            await session.commit()

    text = f"Готово! Напомню {hours_text(hours)}."
    await callback.message.edit_text(text)
    await callback.answer()


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

    now = now_msk()
    lines = ["Твои занятия:\n"]
    for lesson in lessons:
        dt = lesson.datetime_start
        mark = "✓" if dt < now else "•"
        line = f"{mark} {dt.strftime('%d.%m.%Y %H:%M')}"
        line += f" — {lesson.title}"
        lines.append(line)

    await message.answer("\n".join(lines))


@dp.message(Command("add_lesson"))
async def cmd_add_lesson(
    message: types.Message,
    state: FSMContext,
):
    uid = message.from_user.id
    if not is_teacher(uid):
        await message.answer("Только для преподавателя.")
        return

    async with async_session() as session:
        q = select(Student).where(
            Student.tg_id != TEACHER_ID
        )
        result = await session.execute(q)
        students = result.scalars().all()

    if not students:
        await message.answer(
            "Нет учеников. Пусть кто-то напишет /start."
        )
        return

    text = "Выбери ученика:"
    await message.answer(
        text,
        reply_markup=students_keyboard(students),
    )
    await state.set_state(AddLesson.student)


@dp.callback_query(
    lambda c: c.data.startswith("st:"),
    AddLesson.student,
)
async def process_student_btn(
    callback: CallbackQuery,
    state: FSMContext,
):
    sid = int(callback.data.split(":")[1])

    async with async_session() as session:
        student = await session.get(Student, sid)

    if not student:
        await callback.answer("Не найден")
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
    await callback.message.edit_text(text)
    await callback.answer()
    await state.set_state(AddLesson.dt)


@dp.message(AddLesson.student)
async def process_student_text(
    message: types.Message,
    state: FSMContext,
):
    try:
        sid = int(message.text.strip())
    except ValueError:
        await message.answer(
            "Выбери ученика кнопкой выше."
        )
        return

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == sid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

    if not student:
        await message.answer("Ученик не найден.")
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
async def process_dt(
    message: types.Message,
    state: FotSMContext,
):
    try: Bot):
        dt = datetime.strptime(
            message.text.strip ->(),
            "%d.%m.%Y %H:%M",
        None )
    except ValueError:
        await message.answer(
            "Неверный формат. Пример: 15.10.2026 18:30"
        )
        return

    await state.update_data(dt=dt)
    await message.answer(
        "Введи название занятия "
        "(или «-», чтобы было «Итальянский»):"
    )
    await state.set_state(AddLesson.title)


@dp.message(AddLesson.title)
async def process_title(
    message: types.Message,
    state: FSMContext,
):
    data = await state.get_data()
    title = message.text.strip()
    if title == "-":
        title = "Итальянский"

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
        q = select(Lesson).order_by(
            Lesson.datetime_start
        )
        result = await session.execute(q)
        lessons = result.scalars().all()

        # Карта id → имя ученика
        q2 = select(Student)
        result2 = await session.execute(q2)
        students = result2.scalars().all()
        students_map = {
            s.id: s.full_name for s in students
        }

    if not lessons:
        await message.answer("Занятий пока нет.")
        return

    now = now_msk()
    future = [l for l in lessons if l.datetime_start >= now]
    past = [l for l in lessons if l.datetime_start < now]

    lines = []

    if future:
        lines.append("📅 Предстоящие:\n")
        for lesson in future:
            name = students_map.get(
                lesson.student_id, "?"
            )
            dt = lesson.datetime_start
            line = f"• {dt.strftime('%d.%m %H:%M')}"
            line += f" — {name}"
            line += f" ({lesson.title})"
            lines.append(line)

    if past:
        lines.append("\n✓ Прошедшие:\n")
        for lesson in past[-10:]:
            name = students_map.get(
                lesson.student_id, "?"
            )
            dt = lesson.datetime_start
            line = f"✓ {dt.strftime('%d.%m %H:%M')}"
            line += f" — {name}"
            lines.append(line)

    await message.answer("\n".join(lines))


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    uid = message.from_user.id
    if not is_teacher(uid):
        await message.answer("Только для преподавателя.")
        return

    async with async_session() as session:
        q = select(Student)
        result = await session.execute(q)
        students = result.scalars().all()

        q2 = select(Lesson)
        result2 = await session.execute(q2)
        lessons = result2.scalars().all()

    now = now_msk()

    lines = ["📊 Статистика:\n"]
    lines.append(f"Учеников: {len(students)}")
    lines.append(f"Всего занятий: {len(lessons)}")

    done = [l for l in lessons if l.datetime_start < now]
    future = [l for l in lessons if l.datetime_start >= now]
    lines.append(f"Проведено: {len(done)}")
    lines.append(f"Предстоит: {len(future)}")

    lines.append("\nПо ученикам:")
    for s in students:
        if s.tg_id == TEACHER_ID:
            continue
        s_lessons = [
            l for l in lessons
            if l.student_id == s.id
        ]
        s_done = len([
            l for l in s_lessons
            if l.datetime_start < now
        ])
        paid = s.paid_lessons or 0
        left = paid - s_done
        lines.append(
            f"• {s.full_name}: "
            f"{s_done} проведено, "
            f"{left} осталось"
        )

    await message.answer("\n".join(lines))


@dp.message(Command("set_paid"))
async def cmd_set_paid(
    message: types.Message,
    state: FSMContext,
):
    uid = message.from_user.id
    if not is_teacher(uid):
        await message.answer("Только для преподавателя.")
        return

    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "Формат: /set_paid ID количество\n"
            "Например: /set_paid 803167669 8"
        )
        return

    try:
        sid = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("ID и число.")
        return

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == sid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

        if not student:
            await message.answer("Ученик не найден.")
            return

        student.paid_lessons = amount
        student.last_payment_reminder = None
        await session.commit()

    await message.answer(
        f"✅ {student.full_name}: "
        f"оплачено {amount} занятий"
    )


# Health-эндпоинт для UptimeRobot
async def health(request):
    return web.Response(text="OK")


async def on_startup(b:
    await init_db()
    logging.info("БД готова")
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
    )
    logging.info("Webhook установлен")
    start_scheduler(bot)


app = web.Application()

handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
    secret_token=WEBHOOK_SECRET,
)
handler.register(app, path=WEBHOOK_PATH)

app.router.add_get("/health", health)

setup_application(app, dp, bot=bot)
dp.startup.register(on_startup)


if __name__ == "__main__":
    print("Сервер запущен")
    web.run_app(
        app,
        host=WEB_SERVER_HOST,
        port=WEB_SERVER_PORT,
    )
