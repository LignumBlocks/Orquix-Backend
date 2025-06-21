from typing import AsyncGenerator

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Importar todos los modelos para que SQLModel.metadata los conozca
from app.models.models import (
    User, Project, ModeratedSynthesis, InteractionEvent, 
    IAPrompt, IAResponse, ContextChunk, Chat, Session
)

engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for FastAPI endpoints."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise 
        finally:
            await session.close() 