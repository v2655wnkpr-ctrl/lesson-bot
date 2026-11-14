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
    """Проверяет занятия: напоминания, ссылки, списание с абонемента"""
    now = now_msk()
    async with async_session() as session:
        # Получаем занятия на ближайшие 24 часа + те, что прошли, но не отмечены как done
        q = select(Lesson).where(
            Lesson.datetime_start >= now - timedelta(hours=3),
            Lesson.datetime_start <= now + timedelta(hours=24)
        )
        r = await session.execute(q)
        lessons = r.scalars().all()
        
        for lesson in lessons:
            q_st = select(Student).where(Student.id == lesson.student_id)
            r_st = await session.execute(q_st)
            st = r_st.scalar_one_or_none()
            if not st: continue
            
            # --- АВТОСПИСАНИЕ С АБОНЕМЕНТА ---
            # Если урок начался больше часа назад и еще не отмечен как проведенный
            if not lesson.is_done and lesson.datetime_start < now - timedelta(hours=1):
                lesson.is_done = True
                balance_before = st.paid_lessons or 0
                
                if balance_before > 0:
                    st.paid_lessons = balance_before - 1
                
                await session.commit()
                
                try:
                    await bot.send_message(
                        TEACHER_ID,
                        f"✅ Урок проведен!\n"
                        f"👤 Ученик: {st.full_name}\n"
                        f"📅 {lesson.datetime_start.strftime('%d.%m %H:%M')}\n"
                        f"💳 Остаток на абонементе: {st.paid_lessons or 0} зан."
                    )
                except Exception:
                    pass
                continue  # Дальше напоминания для этого урока слать не надо
            
            # --- НАПОМИНАНИЯ ---
            remind_hours = st.custom_hours_before if st.custom_hours_before is not None else 2
            
            local_lesson_time = lesson.datetime_start + timedelta(hours=st.timezone_offset)
            local_now = now + timedelta(hours=st.timezone_offset)
            
            diff_minutes = (local_lesson_time - local_now).total_seconds() / 60
            
            # 1. Напоминание за N часов (окно ±1 минута)
            target_minutes = remind_hours * 60
            if (target_minutes - 1) <= diff_minutes <= (target_minutes + 1):
                text_st = (
                    f"🔔 Напоминание: у вас занятие через {remind_hours} ч.\n\n"
                    f"📅 {local_lesson_time.strftime('%d.%m %H:%M')}\n"
                    f"📚 {lesson.title}"
                )
                try:
                    await bot.send_message(st.tg_id, text_st)
                except Exception:
                    pass
                    
            # 2. Ссылка на урок за 30 минут (окно 29-30 минут)
            if 29 <= diff_minutes <= 30:
                link = "https://telemost.yandex.ru/j/55769145881207"
                
                # Ученику
                text_st_link = (
                    f"🔗 Скоро урок! Подключайтесь:\n\n"
                    f"📅 {local_lesson_time.strftime('%H:%M')}\n"
                    f"Ссылка: {link}"
                )
                try:
                    await bot.send_message(st.tg_id, text_st_link)
                except Exception:
                    pass
                    
                # Преподу
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