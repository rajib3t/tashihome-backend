from app.repositories.city_repository import CityRepository
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.database import get_db
from app.repositories.country_repository import CountryRepository
from app.repositories.setting_repository import SettingRepository
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


async def get_setting_repository(
    db: AsyncSession = Depends(get_db),
) -> SettingRepository:
   
    return SettingRepository(db)

async def get_country_repository(
    db: AsyncSession = Depends(get_db),
) -> CountryRepository:
    return CountryRepository(db)

async def get_city_repository(
    db: AsyncSession = Depends(get_db),
) -> CityRepository:
    return CityRepository(db)