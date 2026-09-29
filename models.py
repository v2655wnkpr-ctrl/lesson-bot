from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Настройки напоминаний (пока не используем, но поля готовим)
    reminder_mode: Mapped[str] = mapped_column(String(20), default="day_of")
    custom_hours_before: Mapped[int | None] = mapped_column(nullable=True)

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan"
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    datetime_start: Mapped[datetime] = mapped_column(DateTime)
    title: Mapped[str] = mapped_column(String(200), default="Занятие")

    student: Mapped["Student"] = relationship(back_populates="lessons")
