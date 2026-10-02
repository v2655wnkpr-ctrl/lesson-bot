import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler,
)
from sqlalchemy import select

from database import async_session
from models import Student, Lesson


MSK = ZoneInfo("Europe/Moscow")

LESSON_LINK = (
    "https://telemost.yandex.ru/j/55769145881207"
)

scheduler = AsyncIOScheduler()


def now_msk() -> datetime:
    return datetime.now(MSK).replace(tzinfo=None)


async def check_lessons(bot):
    now = now_msk()

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

                # Отмечаем прошедшее занятие как проведённое
                if mins < -1 and not lesson.is_done:
                    lesson.is_done = True
                    await session.commit()

            # Напоминание об оплате
            await check_payment(bot, student, session)


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


async def check_payment(bot, student, session):
    """Напоминает об оплате, если занятия заканчиваются."""
    # Сколько проведено занятий всего
    q = select(Lesson).where(
        Lesson.student_id == student.id,
        Lesson.is_done == True,
    )
    result = await session.execute(q)
    done = len(result.scalars().all())

    # Сколько оплачено
    paid = student.paid_lessons or 0

    # Осталось занятий
    left = paid - done

    # Если осталось 1 занятие — напоминаем
    if left == 1:
        now = now_msk()
        last = student.last_payment_reminder
        if last is None or (now - last).days >= 1:
            text = (
                "💰 Напоминание об оплате\n\n"
                "У тебя осталось 1 занятие. "
                "Пора оплатить следующий блок."
            )
            try:
                await bot.send_message(
                    student.tg_id, text
                )
                student.last_payment_reminder = now
                await session.commit()
            except Exception as e:
                logging.error(f"Ошибка оплаты: {e}")


def start_scheduler(bot):
    scheduler.add_job(
        check_lessons,
        "interval",
        minutes=1,
        args=[bot],
    )
    scheduler.start()
    logging.info("Планировщик запущен")