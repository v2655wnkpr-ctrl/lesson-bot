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
TEACHER_LINK = "https://t.me/alinaaait"

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


class PayFlow(StatesGroup):
    choosing_student = State()


class FindStudent(StatesGroup):
    query = State()


def is_teacher(uid: int) -> bool:
    return uid == TEACHER_ID


# ---------- Клавиатуры ----------

def main_menu_student() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 Мои занятия",
                callback_data="menu:lessons",
            ),
            InlineKeyboardButton(
                text="⚙️ Напоминания",
                callback_data="menu:settings",
            ),
        ],
        [
            InlineKeyboardButton(
                text="💬 Связаться",
                url=TEACHER_LINK,
            ),
            InlineKeyboardButton(
                text="ℹ️ Помощь",
                callback_data="menu:help",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_menu_teacher() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ Добавить занятие",
                callback_data="menu:add",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📋 Все занятия",
                callback_data="menu:list",
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="menu:stats",
            ),
        ],
        [
            InlineKeyboardButton(
                text="💰 Оплата",
                callback_data="menu:pay",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔍 Найти ученика",
                callback_data="menu:find",
            ),
            InlineKeyboardButton(
                text="👥 Все ученики",
                callback_data="menu:students",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_main(cb: str = "menu:main") -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=cb,
        ),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def hours_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="За 1 час",
                callback_data="h:1",
            ),
            InlineKeyboardButton(
                text="За 3 часа",
                callback_data="h:3",
            ),
        ],
        [
            InlineKeyboardButton(
                text="За 1 день",
                callback_data="h:24",
            ),
            InlineKeyboardButton(
                text="За 2 дня",
                callback_data="h:48",
            ),
        ],
        [
            InlineKeyboardButton(
                text="За неделю",
                callback_data="h:168",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="menu:main",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def pay_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="💳 Оплата после урока",
                callback_data="pay:after",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⏰ Абонемент закончился",
                callback_data="pay:end",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="menu:main",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def tariffs_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="30 мин, 1 раз/нед — 2000₽",
                callback_data="tar:30_1",
            ),
        ],
        [
            InlineKeyboardButton(
                text="30 мин, 2 раза/нед — 4000₽",
                callback_data="tar:30_2",
            ),
        ],
        [
            InlineKeyboardButton(
                text="60 мин, 1 раз/нед — 4000₽",
                callback_data="tar:60_1",
            ),
        ],
        [
            InlineKeyboardButton(
                text="60 мин, 2 раза/нед — 9000₽",
                callback_data="tar:60_2",
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


# ---------- Тексты ----------

def text_pay_after() -> str:
    return (
        "Спасибо за занятие! 🤍\n\n"
        "💳 Стоимость урока:\n"
        "• 60 мин — 1200 ₽\n"
        "• 30 мин — 600 ₽\n\n"
        "Перевод по номеру телефона:\n"
        "+7 938 550-19-00\n"
        "Ozon Банк\n\n"
        "⚠️ Перевод на другой банк "
        "считается неоплаченным занятием.\n\n"
        "Хотите сэкономить? "
        "Посмотрите абонементы 👇"
    )


def text_pay_end() -> str:
    return (
        "Ваш абонемент подошёл к концу 🤍\n\n"
        "Спасибо, что занимаетесь со мной!\n\n"
        "Если хотите продолжить — "
        "выберите подходящий вариант "
        "и оплатите по реквизитам ниже.\n\n"
        "После оплаты я подтвержу продление "
        "и мы продолжим занятия по расписанию."
    )


def text_tariffs() -> str:
    return (
        "💛 Абонементы (со скидкой)\n\n"
        "Занятия по 30 минут:\n"
        "• 1 раз/нед — 2000 ₽\n"
        "• 2 раза/нед — 4000 ₽\n\n"
        "Занятия по 60 минут:\n"
        "• 1 раз/нед — 4000 ₽\n"
        "• 2 раза/нед — 9000 ₽\n\n"
        "Оплата — по тем же реквизитам:\n"
        "+7 938 550-19-00, Ozon Банк\n\n"
        "Выбери подходящий вариант 👇"
    )


def text_help() -> str:
    return (
        "ℹ️ Помощь\n\n"
        "Этот бот помогает следить "
        "за занятиями итальянского.\n\n"
        "• Настрой напоминания, "
        "чтобы не пропустить урок\n"
        "• За 30 минут до занятия "
        "придёт ссылка на встречу\n"
        "• Оплата — по реквизитам "
        "из сообщений\n\n"
        "По всем вопросам: @alinaaait"
    )


# ---------- Хендлеры ----------

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

            if uid != TEACHER_ID:
                text = (
                    "🆕 Новый ученик!\n\n"
                    f"{user.full_name}\n"
                    f"@{user.username or '—'}\n"
                    f"ID: {uid}"
                )
                try:
                    await bot.send_message(
                        TEACHER_ID, text
                    )
                except Exception as e:
                    logging.error(
                        f"Ошибка увед: {e}"
                    )

    if is_teacher(uid):
        text = (
            "👋 Привет, преподаватель!\n\n"
            "Выбери действие:"
        )
        kb = main_menu_teacher()
    else:
        text = (
            f"👋 Привет, {user.full_name}!\n\n"
            "Я помогу тебе следить "
            "за занятиями итальянского."
        )
        kb = main_menu_student()

    await message.answer(text, reply_markup=kb)


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    uid = message.from_user.id
    if is_teacher(uid):
        await message.answer(
            "Главное меню:",
            reply_markup=main_menu_teacher(),
        )
    else:
        await message.answer(
            "Главное меню:",
            reply_markup=main_menu_student(),
        )


@dp.message(Command("pay"))
async def cmd_pay(message: types.Message):
    uid = message.from_user.id
    if not is_teacher(uid):
        await message.answer("Только для преподавателя.")
        return

    await message.answer(
        "💰 Оплата и напоминания\n\n"
        "Что отправить?",
        reply_markup=pay_menu(),
    )


# ---------- Меню (callbacks) ----------

@dp.callback_query(lambda c: c.data == "menu:main")
async def cb_main(callback: CallbackQuery):
    uid = callback.from_user.id
    if is_teacher(uid):
        text = "Главное меню:"
        kb = main_menu_teacher()
    else:
        text = "Главное меню:"
        kb = main_menu_student()

    await callback.message.edit_text(
        text, reply_markup=kb
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "menu:help")
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text(
        text_help(),
        reply_markup=back_to_main(),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "menu:settings")
async def cb_settings(callback: CallbackQuery):
    uid = callback.from_user.id

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == uid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

    if not student:
        await callback.answer("Сначала /start")
        return

    hours = student.custom_hours_before or 2
    text = (
        f"⚙️ Напоминания\n\n"
        f"Сейчас напоминаю "
        f"{hours_text(hours)}.\n\n"
        "Выбери, за сколько напоминать:"
    )
    await callback.message.edit_text(
        text, reply_markup=hours_keyboard()
    )
    await callback.answer()


@dp.callback_query(
    lambda c: c.data.startswith("h:")
)
async def cb_hours(callback: CallbackQuery):
    hours = int(callback.data.split(":")[1])
    uid = callback.from_user.id

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == uid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

        if student:
            student.custom_hours_before = hours
            await session.commit()

    text = (
        f"✅ Готово!\n\n"
        f"Буду напоминать "
        f"{hours_text(hours)} до занятия."
    )
    await callback.message.edit_text(
        text, reply_markup=back_to_main()
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "menu:lessons")
async def cb_lessons(callback: CallbackQuery):
    uid = callback.from_user.id

    async with async_session() as session:
        q = select(Student).where(Student.tg_id == uid)
        result = await session.execute(q)
        student = result.scalar_one_or_none()

        if not student:
            await callback.answer("Сначала /start")
            return

        q2 = (
            select(Lesson)
            .where(Lesson.student_id == student.id)
            .order_by(Lesson.datetime_start)
        )
        result2 = await session.execute(q2)
        lessons = result2.scalars().all()

    if not lessons:
        await callback.message.edit_text(
            "📅 У тебя пока нет занятий.",
            reply_markup=back_to_main(),
        )
        await callback.answer()
        return

    now = now_msk()
    lines = ["📅 Твои занятия:\n"]
    for lesson in lessons:
        dt = lesson.datetime_start
        mark = "✓" if dt < now else "•"
        line = f"{mark} "
        line += dt.strftime("%d.%m.%Y %H:%M")
        line += f" — {lesson.title}"
        lines.append(line)

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_main(),
    )
    await callback.answer()


# ---------- Меню преподавателя ----------

@dp.callback_query(lambda c: c.data == "menu:add")
async def cb_add(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_teacher(uid):
        await callback.answer("Только для препода")
        return

    async with async_session() as session:
        q = select(Student).where(
            Student.tg_id != TEACHER_ID
        )
        result = await session.execute(q)
        students = result.scalars().all()

    if not students:
        await callback.message.edit_text(
            "Нет учеников. "
            "Пусть кто-то напишет /start.",
            reply_markup=back_to_main(),
        )
        await callback.answer()
        return

    lines = ["👥 Выбери ученика:\n"]
    for i, s in enumerate(students, 1):
        un = s.username or "—"
        lines.append(f"{i}. {s.full_name} (@{un})")

    lines.append(
        f"\nНапиши номер (1–{len(students)})"
        f" или @username:"
    )

    state_data = {
        f"student_{i}": s.id
        for i, s in enumerate(students, 1)
    }
    state_data["total"] = len(students)

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_main(),
    )
    await callback.answer()

    state = dp.fsm.get_context(
        bot=bot,
        chat_id=callback.message.chat.id,
        user_id=uid,
    )
    await state.update_data(**state_data)
    await state.set_state(AddLesson.student)


@dp.callback_query(lambda c: c.data == "menu:list")
async def cb_list(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_teacher(uid):
        await callback.answer("Только для препода")
        return

    async with async_session() as session:
        q = select(Lesson).order_by(
            Lesson.datetime_start
        )
        result = await session.execute(q)
        lessons = result.scalars().all()

        q2 = select(Student)
        result2 = await session.execute(q2)
        students = result2.scalars().all()
        s_map = {
            s.id: s.full_name for s in students
        }

    if not lessons:
        await callback.message.edit_text(
            "📋 Занятий пока нет.",
            reply_markup=back_to_main(),
        )
        await callback.answer()
        return

    now = now_msk()
    future = [
        l for l in lessons
        if l.datetime_start >= now
    ]
    past = [
        l for l in lessons
        if l.datetime_start < now
    ]

    lines = []
    if future:
        lines.append("📅 Предстоящие:\n")
        for lesson in future[:20]:
            name = s_map.get(
                lesson.student_id, "?"
            )
            dt = lesson.datetime_start
            line = "• "
            line += dt.strftime("%d.%m %H:%M")
            line += f" — {name}"
            lines.append(line)

    if past:
        lines.append("\n✓ Прошедшие:\n")
        for lesson in past[-10:]:
            name = s_map.get(
                lesson.student_id, "?"
            )
            dt = lesson.datetime_start
            line = "✓ "
            line += dt.strftime("%d.%m %H:%M")
            line += f" — {name}"
            lines.append(line)

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_main(),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "menu:stats")
async def cb_stats(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_teacher(uid):
        await callback.answer("Только для препода")
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

    done = [
        l for l in lessons
        if l.datetime_start < now
    ]
    future = [
        l for l in lessons
        if l.datetime_start >= now
    ]
    lines.append(f"Проведено: {len(done)}")
    lines.append(f"Предстоит: {len(future)}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_main(),
    )
    await callback.answer()


# ---------- Все ученики ----------

@dp.callback_query(lambda c: c.data == "menu:students")
async def cb_students(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_teacher(uid):
        await callback.answer("Только для препода")
        return

    async with async_session() as session:
        q = select(Student).where(
            Student.tg_id != TEACHER_ID
        )
        result = await session.execute(q)
        students = result.scalars().all()

    if not students:
        await callback.message.edit_text(
            "Учеников пока нет.",
            reply_markup=back_to_main(),
        )
        await callback.answer()
        return

    lines = ["👥 Ученики:\n"]
    for i, s in enumerate(students, 1):
        un = s.username or "—"
        line = f"{i}. {s.full_name}"
        line += f" (@{un})"
        lines.append(line)

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_main(),
    )
    await callback.answer()


# ---------- Поиск ученика ----------

@dp.callback_query(lambda c: c.data == "menu:find")
async def cb_find(
    callback: CallbackQuery,
    state: FSMContext,
):
    uid = callback.from_user.id
    if not is_teacher(uid):
        await callback.answer("Только для препода")
        return

    text = (
        "🔍 Поиск ученика\n\n"
        "Напиши @username или имя:\n\n"
        "Например: @alina\n"
        "или: Алина"
    )
    await callback.message.edit_text(
        text,
        reply_markup=back_to_main(),
    )
    await callback.answer()
    await state.set_state(FindStudent.query)


@dp.message(FindStudent.query)
async def find_query(
    message: types.Message,
    state: FSMContext,
):
    uid = message.from_user.id
    if not is_teacher(uid):
        return

    query = message.text.strip()
    query_low = query.lower().lstrip("@")

    async with async_session() as session:
        q = select(Student)
        result = await session.execute(q)
        all_students = result.scalars().all()

    found = []
    for s in all_students:
        if s.tg_id == TEACHER_ID:
            continue
        name_low = s.full_name.lower()
        un_low = (s.username or "").lower()
        if query_low in name_low:
            found.append(s)
        elif query_low == un_low:
            found.append(s)

    if not found:
        await message.answer(
            "❌ Ученик не найден.\n\n"
            "Проверь @username или имя.",
            reply_markup=back_to_main(),
        )
        await state.clear()
        return

    if len(found) > 1:
        lines = ["🔍 Найдено несколько:\n"]
        for i, s in enumerate(found, 1):
            un = s.username or "—"
            line = f"{i}. {s.full_name}"
            line += f" (@{un})"
            lines.append(line)

        lines.append(
            "\nУточни поиск "
            "(напиши @username точнее):"
        )
        await message.answer("\n".join(lines))
        return

    student = found[0]
    await show_card(message, student)
    await state.clear()


async def show_card(message, student):
    async with async_session() as session:
        q = select(Lesson).where(
            Lesson.student_id == student.id
        )
        result = await session.execute(q)
        lessons = result.scalars().all()

    now = now_msk()
    done = len([
        l for l in lessons
        if l.datetime_start < now
    ])
    future = len([
        l for l in lessons
        if l.datetime_start >= now
    ])

    un = student.username or "—"
    text = (
        f"👤 {student.full_name}\n\n"
        f"@{un}\n"
        f"ID: {student.tg_id}\n\n"
        f"Проведено занятий: {done}\n"
        f"Предстоит: {future}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Занятие",
                callback_data=f"act:add:{student.id}",
            ),
            InlineKeyboardButton(
                text="💰 Оплата",
                callback_data=f"act:pay:{student.id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="menu:main",
            ),
        ],
    ])

    await message.answer(text, reply_markup=kb)


# ---------- Оплата ----------

@dp.callback_query(lambda c: c.data == "menu:pay")
async def cb_pay(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_teacher(uid):
        await callback.answer("Только для препода")
        return

    await callback.message.edit_text(
        "💰 Оплата и напоминания\n\n"
        "Что отправить?",
        reply_markup=pay_menu(),
    )
    await callback.answer()


@dp.callback_query(
    lambda c: c.data in ("pay:after", "pay:end")
)
async def cb_pay_choose(
    callback: CallbackQuery,
    state: FSMContext,
):
    uid = callback.from_user.id
    if not is_teacher(uid):
        await callback.answer("Только для препода")
        return

    mode = callback.data.split(":")[1]

    async with async_session() as session:
        q = select(Student).where(
            Student.tg_id != TEACHER_ID
        )
        result = await session.execute(q)
        students = result.scalars().all()

    if not students:
        await callback.message.edit_text(
            "Нет учеников.",
            reply_markup=back_to_main("menu:pay"),
        )
        await callback.answer()
        return

    lines = ["👥 Кому отправить?\n"]
    for i, s in enumerate(students, 1):
        un = s.username or "—"
        line = f"{i}. {s.full_name}"
        line += f" (@{un})"
        lines.append(line)

    lines.append(
        f"\nНапиши номер "
        f"(1–{len(students)}) "
        f"или @username:"
    )

    data = {"mode": mode, "total": len(students)}
    for i, s in enumerate(students, 1):
        data[f"st_{i}"] = s.tg_id

    await state.update_data(**data)
    await state.set_state(PayFlow.choosing_student)

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_main("menu:pay"),
    )
    await callback.answer()


@dp.message(PayFlow.choosing_student)
async def pay_send(
    message: types.Message,
    state: FSMContext,
):
    uid = message.from_user.id
    if not is_teacher(uid):
        return

    data = await state.get_data()
    total = data.get("total", 0)
    mode = data.get("mode")
    text_in = message.text.strip()

    student_tg = None

    # Если число
    if text_in.isdigit():
        num = int(text_in)
        if 1 <= num <= total:
            student_tg = data.get(f"st_{num}")

    # Если @username или имя
    if student_tg is None:
        query_low = text_in.lower().lstrip("@")
        async with async_session() as session:
            q = select(Student)
            result = await session.execute(q)
            all_s = result.scalars().all()

        for s in all_s:
            if s.tg_id == TEACHER_ID:
                continue
            un_low = (s.username or "").lower()
            nm_low = s.full_name.lower()
            if query_low == un_low:
                student_tg = s.tg_id
                break
            if query_low in nm_low:
                student_tg = s.tg_id
                break

    if student_tg is None:
        await message.answer(
            "Не нашёл. Напиши номер "
            "или @username точнее."
        )
        return

    if mode == "after":
        text = text_pay_after()
    else:
        text = text_pay_end()

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📋 Посмотреть абонементы",
            callback_data="show:tariffs",
        ),
    ]])

    try:
        await bot.send_message(
            student_tg, text, reply_markup=kb
        )
    except Exception as e:
        await message.answer(
            f"Ошибка отправки: {e}"
        )
        await state.clear()
        return

    await state.clear()
    await message.answer(
        "✅ Сообщение отправлено.",
        reply_markup=back_to_main("menu:pay"),
    )


# ---------- Ученик: тарифы ----------

@dp.callback_query(
    lambda c: c.data == "show:tariffs"
)
async def cb_show_tariffs(
    callback: CallbackQuery,
):
    await callback.message.edit_text(
        text_tariffs(),
        reply_markup=tariffs_keyboard(),
    )
    await callback.answer()


@dp.callback_query(
    lambda c: c.data.startswith("tar:")
)
async def cb_tariff_chosen(
    callback: CallbackQuery,
):
    tar = callback.data.split(":")[1]

    tariffs = {
        "30_1": "30 мин, 1 раз/нед — 2000 ₽",
        "30_2": "30 мин, 2 раза/нед — 4000 ₽",
        "60_1": "60 мин, 1 раз/нед — 4000 ₽",
        "60_2": "60 мин, 2 раза/нед — 9000 ₽",
    }
    chosen = tariffs.get(tar, "?")
    user = callback.from_user

    text = (
        "🔔 Заявка на абонемент\n\n"
        f"Ученик: {user.full_name}\n"
        f"Username: @{user.username or '—'}\n"
        f"Тариф: {chosen}\n\n"
        "Свяжись с учеником."
    )

    try:
        await bot.send_message(TEACHER_ID, text)
    except Exception as e:
        logging.error(f"Ошибка увед: {e}")

    await callback.message.edit_text(
        "✅ Заявка отправлена!\n\n"
        "Я свяжусь с тобой, "
        "чтобы подтвердить абонемент.",
    )
    await callback.answer()


# ---------- Добавление занятия ----------

@dp.message(AddLesson.student)
async def add_student_num(
    message: types.Message,
    state: FSMContext,
):
    data = await state.get_data()
    total = data.get("total", 0)
    text_in = message.text.strip()
    student_id = None

    if text_in.isdigit():
        num = int(text_in)
        if 1 <= num <= total:
            student_id = data.get(f"student_{num}")

    if student_id is None:
        query_low = text_in.lower().lstrip("@")
        async with async_session() as session:
            q = select(Student)
            result = await session.execute(q)
            all_s = result.scalars().all()

        for s in all_s:
            if s.tg_id == TEACHER_ID:
                continue
            un_low = (s.username or "").lower()
            nm_low = s.full_name.lower()
            if query_low == un_low:
                student_id = s.id
                break
            if query_low in nm_low:
                student_id = s.id
                break

    if student_id is None:
        await message.answer(
            "Не нашёл. Напиши номер "
            "или @username точнее."
        )
        return

    async with async_session() as session:
        student = await session.get(
            Student, student_id
        )

    if not student:
        await message.answer("Ученик не найден.")
        await state.clear()
        return

    await state.update_data(
        sid=student.id,
        sname=student.full_name,
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
async def add_dt(
    message: types.Message,
    state: FSMContext,
):
    try:
        dt = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y %H:%M",
        )
    except ValueError:
        await message.answer(
            "Неверный формат. "
            "Пример: 15.10.2026 18:30"
        )
        return

    await state.update_data(dt=dt)
    await message.answer(
        "Введи название занятия "
        "(или «-», чтобы было «Итальянский»):"
    )
    await state.set_state(AddLesson.title)


@dp.message(AddLesson.title)
async def add_title(
    message: types.Message,
    state: FSMContext,
):
    data = await state.get_data()
    title = message.text.strip()
    if title == "-":
        title = "Итальянский"

    async with async_session() as session:
        lesson = Lesson(
            student_id=data["sid"],
            datetime_start=data["dt"],
            title=title,
        )
        session.add(lesson)
        await session.commit()

    dt = data["dt"]
    text = (
        "✅ Занятие добавлено!\n\n"
        f"Ученик: {data['sname']}\n"
        f"Дата: {dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"Название: {title}"
    )
    await message.answer(
        text,
        reply_markup=main_menu_teacher(),
    )
    await state.clear()


# ---------- /set_paid ----------

@dp.message(Command("set_paid"))
async def cmd_set_paid(message: types.Message):
    uid = message.from_user.id
    if not is_teacher(uid):
        await message.answer("Только для препода.")