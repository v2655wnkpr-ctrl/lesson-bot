import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from database import async_session
from models import Lesson, Student, LessonSlot

# ID преподавателя итальянского бота
TEACHER_ID = 932503024 

scheduler = AsyncIOScheduler()

def now_msk() -> datetime:
    # Возвращает текущее время по Москве (UTC+3)
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=3)

async def check_lessons(bot):
    """Проверяет занятия и рассылает напоминания"""
    now = now_msk()
    async with async_session() as session:
        # Получаем занятия на ближайшие 24 часа
        q = select(Lesson).where(Lesson.datetime_start >= now, Lesson.datetime_start <= now + timedelta(hours=24))
        r = await session.execute(q)
        lessons = r.scalars().all()
        
        for lesson in lessons:
            q_st = select(Student).where(Student.id == lesson.student_id)
            r_st = await session.execute(q_st)
            st = r_st.scalar_one_or_none()
            if not st: continue
            
            # Настройки напоминания ученика
            remind_hours = st.custom_hours_before if st.custom_hours_before is not None else 2
            
            # Учитываем часовой пояс ученика
            local_lesson_time = lesson.datetime_start + timedelta(hours=st.timezone_offset)
            local_now = now + timedelta(hours=st.timezone_offset)
            
            diff_minutes = (local_lesson_time - local_now).total_seconds() / 60
            
            # 1. Напоминание за N часов (добавил +/- 1 минуту на погрешность сервера)
            target_minutes = remind_hours * 60
            if (target_minutes - 1) <= diff_minutes <= (target_minutes + 1):
                text_st = f"🔔 Напоминание: у тебя занятие через {remind_hours} ч.\n\n📅 {local_lesson_time.strftime('%d.%m %H:%M')}\n📚 {lesson.title}"
                try:
                    await bot.send_message(st.tg_id, text_st)
                except Exception:
                    pass
                    
            # 2. Ссылка на урок за 30 минут (ОКНО 29-30 И ОТПРАВКА ПРЕПОДУ)
            if 29 <= diff_minutes <= 30:
                link = "https://telemost.yandex.ru/j/55769145881207" # <--- ТВОЯ ССЫЛКА ТУТ
                
                # Ссылка для ученика
                text_st_link = (
                    f"🔗 Скоро урок! Подключайся:\n\n"
                    f"📅 {local_lesson_time.strftime('%H:%M')}\n"
                    f"Ссылка: {link}"
                )
                try:
                    await bot.send_message(st.tg_id, text_st_link)
                except Exception:
                    pass
                    
                # Уведомление для препода
                text_tch = (
                    f"🔔 Скоро урок у ученика: {st.full_name}\n"
                    f"📅 Время: {local_lesson_time.strftime('%d.%m %H:%M')}\n"
                    f"Ссылка: {link}"
                )
                try:
                    await bot.send_message(TEACHER_ID, text_tch)
                except Exception:
                    pass

def start_scheduler(bot):
    scheduler.add_job(check_lessons, 'interval', minutes=1, args=[bot])
    scheduler.start()
    logging.info("Планировщик запущен")