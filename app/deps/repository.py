from app.repositories.facility_repository import  FacilityRepository
from app.repositories.amenity_repository import AmenityRepository
from app.repositories.room_type_repository import RoomTypeRepository
from app.repositories.city_repository import CityRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.address_repository import AddressRepository
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.database import get_db
from app.repositories.country_repository import CountryRepository
from app.repositories.setting_repository import SettingRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.property_asset_repository import PropertyAssetRepository
from app.repositories.property_room_type_repository import PropertyRoomTypeRepository
from app.repositories.property_facility_repository import PropertyFacilityRepository
from app.repositories.property_amenity_repository import PropertyAmenityRepository
from app.repositories.property_food_option_repository import PropertyFoodOptionRepository

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

async def get_location_repository(
    db: AsyncSession = Depends(get_db),
) -> LocationRepository:
    return LocationRepository(db)


async def get_attribute_repository(
    db: AsyncSession = Depends(get_db),
) -> FacilityRepository:
    return FacilityRepository(db)


async def get_amenity_repository(
    db: AsyncSession = Depends(get_db),
) -> AmenityRepository:
    return AmenityRepository(db)


async def get_room_type_repository(
    db: AsyncSession = Depends(get_db),
) -> RoomTypeRepository:
    return RoomTypeRepository(db)


async def get_company_repository(
    db: AsyncSession = Depends(get_db),
) -> CompanyRepository:
    return CompanyRepository(db)


async def get_address_repository(
    db: AsyncSession = Depends(get_db),
) -> AddressRepository:
    return AddressRepository(db)


async def get_property_repository(
    db: AsyncSession = Depends(get_db),
) -> PropertyRepository:
    return PropertyRepository(db)


async def get_property_asset_repository(
    db: AsyncSession = Depends(get_db),
) -> PropertyAssetRepository:
    return PropertyAssetRepository(db)


async def get_property_room_type_repository(
    db: AsyncSession = Depends(get_db),
) -> PropertyRoomTypeRepository:
    return PropertyRoomTypeRepository(db)


async def get_property_facility_repository(
    db: AsyncSession = Depends(get_db),
) -> PropertyFacilityRepository:
    return PropertyFacilityRepository(db)


async def get_property_amenity_repository(
    db: AsyncSession = Depends(get_db),
) -> PropertyAmenityRepository:
    return PropertyAmenityRepository(db)


async def get_property_food_option_repository(
    db: AsyncSession = Depends(get_db),
) -> PropertyFoodOptionRepository:
    return PropertyFoodOptionRepository(db)
