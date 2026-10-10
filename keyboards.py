from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


TEACHER_LINK = "https://t.me/alinaaait"

# Анимированные ID
E_LESSONS = "5343968081150486424"
E_SETTINGS = "5343705388065763490"
E_CONTACT = "5253967574038752898"
E_HELP = "5344015111042378193"
E_RESCHED = "5312111690240763536"
E_DELETE = "5341285689390542260"
E_LIST = "5343835843402411085"
E_STATS = "5343846413316925467"
E_SETPAID = "5343928112184831466"
E_FIND = "5343803218830829094"
E_STUDENTS = "5361658604766110429"


def main_menu_student():
    b = [
        [
            InlineKeyboardButton(
                text="Мои занятия",
                callback_data="menu:lessons",
                icon_custom_emoji_id=E_LESSONS,
            ),
            InlineKeyboardButton(
                text="Напоминания",
                callback_data="menu:settings",
                icon_custom_emoji_id=E_SETTINGS,
            ),
        ],
        [
            InlineKeyboardButton(
                text="Связаться",
                url=TEACHER_LINK,
                icon_custom_emoji_id=E_CONTACT,
            ),
            InlineKeyboardButton(
                text="Помощь",
                callback_data="menu:help",
                icon_custom_emoji_id=E_HELP,
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
                text="Перенести",
                callback_data="menu:reschedule",
                icon_custom_emoji_id=E_RESCHED,
            ),
            InlineKeyboardButton(
                text="Удалить",
                callback_data="menu:delete",
                icon_custom_emoji_id=E_DELETE,
            ),
        ],
        [
            InlineKeyboardButton(
                text="Все занятия",
                callback_data="menu:list",
                icon_custom_emoji_id=E_LIST,
            ),
            InlineKeyboardButton(
                text="Статистика",
                callback_data="menu:stats",
                icon_custom_emoji_id=E_STATS,
            ),
        ],
        [
            InlineKeyboardButton(
                text="💰 Оплата",
                callback_data="menu:pay",
            ),
            InlineKeyboardButton(
                text="set_paid",
                callback_data="sp:open",
                icon_custom_emoji_id=E_SETPAID,
            ),
        ],
        [
            InlineKeyboardButton(
                text="Найти",
                callback_data="menu:find",
                icon_custom_emoji_id=E_FIND,
            ),
            InlineKeyboardButton(
                text="Ученики",
                callback_data="menu:students",
                icon_custom_emoji_id=E_STUDENTS,
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
                text="30 мин, 1 раз — 2000₽/мес",
                callback_data="tar:30_1",
            ),
        ],
        [
            InlineKeyboardButton(
                text="30 мин, 2 раза — 4000₽/мес",
                callback_data="tar:30_2",
            ),
        ],
        [
            InlineKeyboardButton(
                text="60 мин, 1 раз — 4000₽/мес",
                callback_data="tar:60_1",
            ),
        ],
        [
            InlineKeyboardButton(
                text="60 мин, 2 раза — 9000₽/мес",
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


def set_paid_students_keyboard(students):
    b = []
    for s in students:
        name = s.full_name
        if len(name) > 28:
            name = name[:28] + "..."
        b.append([
            InlineKeyboardButton(
                text=name,
                callback_data=f"sp:{s.id}",
            )
        ])
    b.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="menu:main",
        ),
    ])
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def set_paid_amounts_keyboard(sid: int):
    b = [
        [
            InlineKeyboardButton(
                text="4 занятия",
                callback_data=f"spa:{sid}:4",
            ),
            InlineKeyboardButton(
                text="8 занятий",
                callback_data=f"spa:{sid}:8",
            ),
        ],
        [
            InlineKeyboardButton(
                text="12 занятий",
                callback_data=f"spa:{sid}:12",
            ),
            InlineKeyboardButton(
                text="16 занятий",
                callback_data=f"spa:{sid}:16",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌ Обнулить",
                callback_data=f"spa:{sid}:0",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="sp:open",
            ),
        ],
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def paid_button_keyboard():
    b = [
        [
            InlineKeyboardButton(
                text="📋 Посмотреть абонементы",
                callback_data="show:tariffs",
            ),
        ],
        [
            InlineKeyboardButton(
                text="💳 Я оплатил(а)",
                callback_data="paid:click",
            ),
        ],
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def back_from_paid_keyboard():
    b = [[
        InlineKeyboardButton(
            text="⬅️ Отмена",
            callback_data="paid:back",
        ),
    ]]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def transfer_keyboard():
    b = [[
        InlineKeyboardButton(
            text="Перенести",
            callback_data="transfer:click",
            icon_custom_emoji_id=E_RESCHED,
        ),
    ]]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def transfer_cancel_keyboard():
    b = [[
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="transfer:cancel",
        ),
    ]]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def lessons_action_keyboard(lessons, action):
    b = []
    for les in lessons[:15]:
        dt = les.datetime_start
        text = dt.strftime("%d.%m %H:%M")
        text += f" — {les.title}"
        b.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"{action}:{les.id}",
            )
        ])
    b.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="menu:main",
        ),
    ])
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )


def confirm_delete_keyboard(lid: int):
    b = [
        [
            InlineKeyboardButton(
                text="Удалить",
                callback_data=f"confirm_del:{lid}",
                icon_custom_emoji_id=E_DELETE,
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="menu:main",
            ),
        ],
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=b
    )