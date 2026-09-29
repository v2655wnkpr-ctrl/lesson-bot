import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler,
)
from sqlalchemy import select

from database import async_session
from models import Student, Lesson


LESSON_LINK = (
    "https://telemost.yandex.ru/j/55769145881207"
)

scheduler = AsyncIOScheduler()


async def check_lessons(bot):
    now = datetime.now()

    async with async_session() as session:
        q = select(Student)
        result = await session.execute(q)
        students = result.scalars().all()

        for student in students:
            hours = student.custom_hours_before
            if hours is None:
                hours = 2

            q2 = select(Lesson).where(
                Lesson.student_id == student.id
            )
            result2 = await session.execute(q2)
            lessons = result2.scalars().all()

            for lesson in lessons:
                diff = lesson.datetime_start - now
                mins = diff.total_seconds() / 60

                target = hours * 60
                if 0 <= target - mins <= 1:
                    await send_reminder(
                        bot, student, lesson
                    )

                if 0 <= 30 - mins <= 1:
                    await send_link(
                        bot, student, lesson
                    )


async def send_reminder(bot, student, lesson):
    dt = lesson.datetime_start
    text = (
        "🔔 Напоминание!\n\n"
        f"Сегодня в {dt.strftime('%H:%M')} — "
        f"{lesson.title}"
    )
    try:
        await bot.send_message(student.tg_id, text)
    except Exception as e:
        logging.error(f"Ошибка напоминания: {e}")


async def send_link(bot, student, lesson):
    dt = lesson.datetime_start
    text = (
        "🔗 Скоро занятие!\n\n"
        f"{lesson.title}, "
        f"{dt.strftime('%H:%M')}\n\n"
        f"Ссылка: {LESSON_LINK}"
    )
    try:
        await bot.send_message(student.tg_id, text)
    except Exception as e:
        logging.error(f"Ошибка ссылки: {e}")


def start_scheduler(bot):
    scheduler.add_job(
        check_lessons,
        "interval",
        minutes=1,
        args=[bot],
    )
    scheduler.start()
    logging.info("Планировщик запущен")
