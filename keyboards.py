import calendar
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TEACHER_LINK = "https://t.me/alinaaait"
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
E_BACK = "5372819657105360167"

def main_menu_student():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мои занятия", callback_data="menu:lessons", icon_custom_emoji_id=E_LESSONS), InlineKeyboardButton(text="Напоминания", callback_data="menu:settings", icon_custom_emoji_id=E_SETTINGS)],
        [InlineKeyboardButton(text="Часовой пояс", callback_data="menu:timezone")],
        [InlineKeyboardButton(text="Связаться", url=TEACHER_LINK, icon_custom_emoji_id=E_CONTACT), InlineKeyboardButton(text="Помощь", callback_data="menu:help", icon_custom_emoji_id=E_HELP)],
        [InlineKeyboardButton(text="🎮 Игра", callback_data="game:menu")],
    ])

def main_menu_teacher():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить занятие", callback_data="menu:add")],
        [InlineKeyboardButton(text="Календарь", callback_data="menu:calendar"), InlineKeyboardButton(text="Слоты", callback_data="menu:slots")],
        [InlineKeyboardButton(text="Перенести", callback_data="menu:reschedule", icon_custom_emoji_id=E_RESCHED), InlineKeyboardButton(text="Удалить", callback_data="menu:delete", icon_custom_emoji_id=E_DELETE)],
        [InlineKeyboardButton(text="Все занятия", callback_data="menu:list", icon_custom_emoji_id=E_LIST), InlineKeyboardButton(text="Статистика", callback_data="menu:stats", icon_custom_emoji_id=E_STATS)],
        [InlineKeyboardButton(text="💰 Оплата", callback_data="menu:pay"), InlineKeyboardButton(text="set_paid", callback_data="sp:open", icon_custom_emoji_id=E_SETPAID)],
        [InlineKeyboardButton(text="Найти", callback_data="menu:find", icon_custom_emoji_id=E_FIND), InlineKeyboardButton(text="Ученики", callback_data="menu:students", icon_custom_emoji_id=E_STUDENTS)],
        [InlineKeyboardButton(text="Часовой пояс", callback_data="menu:timezone")],
        [InlineKeyboardButton(text="🎮 Слова для игры", callback_data="game:admin_menu")],
        [InlineKeyboardButton(text="🎮 Игра", callback_data="game:menu")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="menu:broadcast")],
    ])

def timezone_offset_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Москва (0)", callback_data="tz:0")], [InlineKeyboardButton(text="Владивосток (+7)", callback_data="tz:7")], [InlineKeyboardButton(text="Другой город", callback_data="tz:other")]])

def calendar_keyboard(year, month, days_with_lessons, free_slots_days=None, prefix="cal"):
    kb = []
    month_name = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь", 7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}[month]
    kb.append([InlineKeyboardButton(text=d, callback_data="cal:ignore") for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]])
    if free_slots_days is None: free_slots_days = set()
    for week in calendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0: row.append(InlineKeyboardButton(text=" ", callback_data="cal:ignore"))
            else:
                mark = ""
                if day in days_with_lessons: mark += "•"
                if day in free_slots_days: mark += "🟢"
                row.append(InlineKeyboardButton(text=f"{day}{mark}", callback_data=f"{prefix}:day:{year}-{month:02d}-{day:02d}"))
        kb.append(row)
    prev_m = month - 1 if month > 1 else 12
    prev_y = year if month > 1 else year - 1
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1
    kb.append([InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:init:{prev_y}:{prev_m}"), InlineKeyboardButton(text=month_name, callback_data="cal:ignore"), InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:init:{next_y}:{next_m}")])
    back_cb = "menu:slots" if prefix == "slot" else "menu:main"
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def time_picker_keyboard(selected_times=None):
    if selected_times is None: selected_times = set()
    hours = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]
    b, row = [], []
    for h in hours:
        mark = "✅" if h in selected_times else ""
        row.append(InlineKeyboardButton(text=f"{mark}{h}", callback_data=f"time:{h}"))
        if len(row) == 4: b.append(row); row = []
    if row: b.append(row)
    b.append([InlineKeyboardButton(text="💾 Сохранить", callback_data="time:save")])
    b.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:slots")])
    return InlineKeyboardMarkup(inline_keyboard=b)

def slots_menu_teacher():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ Открыть слоты", callback_data="slot:show_calendar")], [InlineKeyboardButton(text="📋 Мои слоты", callback_data="slot:list")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]])

def slots_delete_keyboard(slots):
    b = [[InlineKeyboardButton(text=f"❌ {s.datetime_start.strftime('%d.%m %H:%M')}", callback_data=f"slot:del:{s.id}")] for s in slots[:20]]
    b.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:slots")])
    return InlineKeyboardMarkup(inline_keyboard=b)

def back_to_main(cb="menu:main"): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=cb)]])
def pay_menu(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💳 После урока", callback_data="pay:after")], [InlineKeyboardButton(text="⏰ Абонемент", callback_data="pay:end")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]])
def tariffs_keyboard(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="30м, 1р — 2000₽", callback_data="tar:30_1")], [InlineKeyboardButton(text="30м, 2р — 4000₽", callback_data="tar:30_2")], [InlineKeyboardButton(text="60м, 1р — 4000₽", callback_data="tar:60_1")], [InlineKeyboardButton(text="60м, 2р — 9000₽", callback_data="tar:60_2")]])

# ВОТ ТУТ ДОБАВЛЕНА КНОПКА ИЗМЕНЕНИЯ ИМЕНИ
def card_keyboard(sid): 
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Занятие", callback_data=f"act:add:{sid}"), InlineKeyboardButton(text="💰 Оплата", callback_data=f"act:pay:{sid}")], 
        [InlineKeyboardButton(text="✏️ Изменить имя", callback_data=f"stdel:setname:{sid}")], # <--- ДОБАВЛЕНО
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"stdel:ask:{sid}")], 
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]
    ])

def set_paid_students_keyboard(students): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=s.full_name[:28], callback_data=f"sp:{s.id}")] for s in students] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]])
def set_paid_amounts_keyboard(sid, current): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="4 зан.", callback_data=f"spa:{sid}:4"), InlineKeyboardButton(text="8 зан.", callback_data=f"spa:{sid}:8")], [InlineKeyboardButton(text="➖ -1", callback_data=f"spa:{sid}:{current-1}"), InlineKeyboardButton(text=f"Сейчас: {current}", callback_data="ignore"), InlineKeyboardButton(text="➕ +1", callback_data=f"spa:{sid}:{current+1}")], [InlineKeyboardButton(text="❌ Обнулить", callback_data=f"spa:{sid}:0")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="sp:open")]])
def confirm_delete_student_keyboard(sid): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🗑 Да", callback_data=f"stdel:{sid}"), InlineKeyboardButton(text="❌ Нет", callback_data="menu:main")]])
def back_from_paid_keyboard(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Отмена", callback_data="paid:back")]])
def transfer_keyboard(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Перенести", callback_data="transfer:click", icon_custom_emoji_id=E_RESCHED)]])
def transfer_cancel_keyboard(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="transfer:cancel")]])
def lessons_action_keyboard(lessons, action): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{l.datetime_start.strftime('%d.%m %H:%M')} — {l.title}", callback_data=f"{action}:{l.id}")] for l in lessons[:15]] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]])
def confirm_delete_keyboard(lid): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Удалить", callback_data=f"confirm_del:{lid}", icon_custom_emoji_id=E_DELETE), InlineKeyboardButton(text="❌ Отмена", callback_data="menu:main")]])
def hours_keyboard(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="1 час", callback_data="h:1"), InlineKeyboardButton(text="3 часа", callback_data="h:3")], [InlineKeyboardButton(text="1 день", callback_data="h:24"), InlineKeyboardButton(text="2 дня", callback_data="h:48")], [InlineKeyboardButton(text="Неделя", callback_data="h:168")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]])
def student_transfer_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Предложить время из слотов", callback_data="transfer:ask_slot")],
        [InlineKeyboardButton(text="Написать причину", callback_data="transfer:click")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]
    ])
def lesson_time_keyboard(date_str: str):
    hours = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]
    b, row = [], []
    for h in hours:
        row.append(InlineKeyboardButton(text=h, callback_data=f"actcal:time:{date_str}:{h}"))
        if len(row) == 4: b.append(row); row = []
    if row: b.append(row)
    b.append([InlineKeyboardButton(text="✍️ Ввести вручную", callback_data="actcal:manual")])
    b.append([InlineKeyboardButton(text="Назад", callback_data="menu:main", icon_custom_emoji_id=E_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=b)
def game_admin_menu(collections):
    b = [[InlineKeyboardButton(text=f"📚 {c.name}", callback_data=f"gcol:view_admin:{c.id}")] for c in collections]
    b.append([InlineKeyboardButton(text="➕ Создать новый блок", callback_data="gcol:create")])
    b.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=b)

def game_col_admin_menu(cid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить слова", callback_data=f"gcol:add_words:{cid}")],
        [InlineKeyboardButton(text="📋 Список слов", callback_data=f"gcol:list_words:{cid}")],
        [InlineKeyboardButton(text="🗑 Удалить блок", callback_data=f"gcol:del_ask:{cid}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="game:admin_menu")]
    ])

def game_words_list_kb(words, cid):
    b = [[InlineKeyboardButton(text=f"❌ {w.italian} - {w.russian}", callback_data=f"gcol:del_word:{w.id}:{cid}")] for w in words[:15]]
    b.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"gcol:view_admin:{cid}")])
    return InlineKeyboardMarkup(inline_keyboard=b)

def game_student_menu(collections):
    b = [[InlineKeyboardButton(text="🎲 Случайные (все слова)", callback_data="game:start_tournament:all")]]
    b += [[InlineKeyboardButton(text=f"📚 {c.name}", callback_data=f"game:start_tournament:{c.id}")] for c in collections]
    b.append([InlineKeyboardButton(text="🏆 Таблица лидеров", callback_data="game:leaderboard")])
    b.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=b)

def game_question_kb(options):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=opt, callback_data=f"game:ans:{opt}")] for opt in options])
def select_student_kb(students, action="add"):
    b = []
    for s in students:
        name = s.custom_name or s.full_name
        b.append([InlineKeyboardButton(text=name, callback_data=f"sel_stud:{action}:{s.id}")])
    b.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=b)