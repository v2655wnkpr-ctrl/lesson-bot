import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from database import async_session
from models import Lesson, Student

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
            
            # Настройки напоминания ученика (по умолчанию 2 часа)
            remind_hours = st.custom_hours_before if st.custom_hours_before is not None else 2
            
            # Учитываем часовой пояс ученика
            local_lesson_time = lesson.datetime_start + timedelta(hours=st.timezone_offset)
            local_now = now + timedelta(hours=st.timezone_offset)
            
            diff_minutes = (local_lesson_time - local_now).total_seconds() / 60
            
            # Напоминание за N часов (проверяем с точностью до минуты)
            if int(diff_minutes) == int(remind_hours * 60):
                text = f"🔔 Напоминание: у вас занятие через {remind_hours} ч.\n\n📅 {local_lesson_time.strftime('%d.%m %H:%M')}\n📚 {lesson.title}"
                try:
                    await bot.send_message(st.tg_id, text)
                except Exception:
                    pass
                    
            # Ссылка на урок за 30 минут
            if int(diff_minutes) == 30:
                text = f"🔗 Скоро урок! Подключайся:\n\n📅 {local_lesson_time.strftime('%H:%M')}\nСсылка: https://telemost.yandex.ru/j/55769145881207"
                try:
                    await bot.send_message(st.tg_id, text)
                except Exception:
                    pass

def start_scheduler(bot):
    scheduler.add_job(check_lessons, 'interval', minutes=1, args=[bot])
    scheduler.start()
    logging.info("Планировщик запущен")