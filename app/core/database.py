from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, AsyncGenerator


from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

ALEMBIC_INI_PATH = Path(__file__).resolve().parents[2] / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = ALEMBIC_INI_PATH.parent / "alembic"

import logging
logger = logging.getLogger(__name__)
def get_database_url() -> str:
    database_url = settings.DATABASE_URL
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set DATABASE_URL in the environment or .env file."
        )
    # Ensure the URL uses an async DB driver (e.g. postgresql+asyncpg://...)
    # If the URL uses a sync driver (e.g. postgresql://) SQLAlchemy async engine
    # will attempt to run sync I/O in an async context and raise
    # `MissingGreenlet: greenlet_spawn has not been called`.
    if "+" not in database_url or "async" not in database_url:
        raise RuntimeError(
            "DATABASE_URL must use an async driver. Example: 'postgresql+asyncpg://user:pass@host:5432/dbname'"
        )

    return database_url


class Database:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine: Optional[AsyncEngine] = None
        self.async_session: Optional[async_sessionmaker[AsyncSession]] = None

    def connect(self) -> None:
        self.engine = create_async_engine(self.db_url, echo=True)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
        logger.info("Database connection established")

    async def disconnect(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.async_session = None
        logger.info("Database connection closed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self.async_session is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")
        async with self.async_session() as session:
            yield session


class Base(DeclarativeBase):
    pass


db = Database(get_database_url())


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with db.get_session() as session:
        yield session






