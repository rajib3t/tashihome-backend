from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db as database


async def get_db() -> AsyncSession:  # type: ignore
    """
    Provide a SQLAlchemy async session scoped to a single HTTP request.

    The session is rolled back on any unhandled exception.
    Write operations are NOT auto-committed here — each repository method
    that mutates state calls ``session.commit()`` explicitly (commit=True default).
    Removing the unconditional commit eliminates a wasted round-trip to the DB
    on every read-only GET request.
    """
    async for session in database.get_session():
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
