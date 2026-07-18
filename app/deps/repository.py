from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.database import get_db
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository

async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


async def get_token_repository(
    db: AsyncSession = Depends(get_db),
) -> TokenRepository:
    return TokenRepository(db)
