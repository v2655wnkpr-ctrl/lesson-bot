from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Файл базы создастся автоматически рядом с ботом
DATABASE_URL = "sqlite+aiosqlite:///lessons.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Создаёт таблицы при первом запуске."""
    from models import Student, Lesson  # импорт внутри, чтобы избежать циклической зависимости
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
