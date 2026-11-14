from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    custom_name: Mapped[str | None] = mapped_column(String(100), nullable=True) # <--- ДОБАВЛЕНО ДЛЯ ИМЕНИ
    
    timezone_offset: Mapped[int] = mapped_column(Integer, default=0) 
    custom_hours_before: Mapped[int] = mapped_column(Integer, default=2)
    paid_lessons: Mapped[int] = mapped_column(Integer, default=0)
    last_payment_reminder: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="student", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    datetime_start: Mapped[datetime] = mapped_column(DateTime)
    title: Mapped[str] = mapped_column(String(200), default="Итальянский")
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    student: Mapped["Student"] = relationship(back_populates="lessons")

class LessonSlot(Base):
    __tablename__ = "lesson_slots" 
    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(BigInteger)
    datetime_start: Mapped[datetime] = mapped_column(DateTime)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)
class GameCollection(Base):
    __tablename__ = "game_collections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)


class GameWord(Base):
    __tablename__ = "game_words"
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("game_collections.id"), nullable=True)
    italian = Column(String, nullable=False)
    russian = Column(String, nullable=False)


class GameResult(Base):
    __tablename__ = "game_results"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    score = Column(Integer, default=0)       # Сколько правильных
    time_taken = Column(Integer, default=0)  # Время в секундах
    date_played = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")