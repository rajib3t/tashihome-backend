from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db as database

async def get_db() -> AsyncSession: # type: ignore
    async for session in database.get_session():
        yield session

        