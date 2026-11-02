import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from database import async_session
from models import Lesson, Student

scheduler = AsyncIOScheduler()
TEACHER_ID = 932503024 # Твой ID итальянского бота

def now_msk() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=3)

async def check_lessons(bot):
    """Проверяет занятия: напоминает, отправляет ссылки, списывает занятия и уведомляет препода"""
    now = now_msk()
    async with async_session() as session:
        # Берем занятия за последние 2 часа (чтобы списать) и на ближайшие 24 часа (чтобы напомнить)
        q = select(Lesson).where(Lesson.datetime_start >= now - timedelta(hours=2), Lesson.datetime_start <= now + timedelta(hours=24))
        r = await session.execute(q)
        lessons = r.scalars().all()
        
        for lesson in lessons:
            q_st = select(Student).where(Student.id == lesson.student_id)
            r_st = await session.execute(q_st)
            st = r_st.scalar_one_or_none()
            if not st: continue
            
            # 1. АВТОСПИСАНИЕ УРОКА (Счетчик)
            if not lesson.is_done and lesson.datetime_start < now:
                lesson.is_done = True
                st.paid_lessons = max(0, (st.paid_lessons or 0) - 1)
                await session.commit()
                
                # Уведомляем препода, что урок прошел и списался
                try:
                    await bot.send_message(
                        TEACHER_ID, 
                        f"✅ Урок проведен!\nУченик: {st.full_name}\nСписано 1 занятие.\nОстаток: {st.paid_lessons}"
                    )
                except Exception:
                    pass

            # 2. НАПОМИНАНИЯ И ССЫЛКИ
            remind_hours = st.custom_hours_before if st.custom_hours_before is not None else 2
            local_lesson_time = lesson.datetime_start + timedelta(hours=st.timezone_offset)
            local_now = now + timedelta(hours=st.timezone_offset)
            diff_minutes = (local_lesson_time - local_now).total_seconds() / 60
            
            # Напоминание за N часов
            if int(diff_minutes) == int(remind_hours * 60):
                text = f"🔔 Напоминание: у тебя занятие через {remind_hours} ч.\n\n📅 {local_lesson_time.strftime('%d.%m %H:%M')}\n📚 {lesson.title}"
                try: await bot.send_message(st.tg_id, text)
                except Exception: pass
                    
            # Ссылка на урок за 30 минут (ВОТ ТУТ ТВОЯ ССЫЛКА)
            if int(diff_minutes) == 30:
                text = (
                    f"🔗 Скоро урок! Подключайся:\n\n"
                    f"📅 {local_lesson_time.strftime('%H:%M')}\n"
                    f"Ссылка: telemost.yandex.ru/j/55769145881207"
                )
                try: await bot.send_message(st.tg_id, text)
                except Exception: pass

def start_scheduler(bot):
    scheduler.add_job(check_lessons, 'interval', minutes=1, args=[bot])
    scheduler.start()
    logging.info("Планировщик запущен")