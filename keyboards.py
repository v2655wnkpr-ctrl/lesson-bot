from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


TEACHER_LINK = "https://t.me/alinaaait"


def main_menu_student():
    b = [
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
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def main_menu_teacher():
    b = [
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
                text="🔍 Найти",
                callback_data="menu:find",
            ),
            InlineKeyboardButton(
                text="👥 Ученики",
                callback_data="menu:students",
            ),
        ],
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def back_to_main(cb: str = "menu:main"):
    b = [[
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=cb,
        ),
    ]]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def hours_keyboard():
    b = [
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
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def pay_menu():
    b = [
        [
            InlineKeyboardButton(
                text="💳 Оплата после урока",
                callback_data="pay:after",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⏰ Абонемент кончился",
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
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def tariffs_keyboard():
    b = [
        [
            InlineKeyboardButton(
                text="30 мин, 1 раз — 2000₽",
                callback_data="tar:30_1",
            ),
        ],
        [
            InlineKeyboardButton(
                text="30 мин, 2 раза — 4000₽",
                callback_data="tar:30_2",
            ),
        ],
        [
            InlineKeyboardButton(
                text="60 мин, 1 раз — 4000₽",
                callback_data="tar:60_1",
            ),
        ],
        [
            InlineKeyboardButton(
                text="60 мин, 2 раза — 9000₽",
                callback_data="tar:60_2",
            ),
        ],
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def card_keyboard(student_id: int):
    b = [
        [
            InlineKeyboardButton(
                text="➕ Занятие",
                callback_data=f"act:add:{student_id}",
            ),
            InlineKeyboardButton(
                text="💰 Оплата",
                callback_data=f"act:pay:{student_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="menu:main",
            ),
        ],
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )
