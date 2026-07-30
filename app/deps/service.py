
from app.repositories.facility_repository import  FacilityRepository
from app.repositories.amenity_repository import AmenityRepository
from app.repositories.room_type_repository import RoomTypeRepository
from app.repositories.location_repository import LocationRepository
from app.services.facility_service import  FacilityService
from app.services.amenity_service import AmenityService
from app.services.room_type_service import RoomTypeService
from app.services.city_service import CityService
from app.repositories.city_repository import CityRepository
from fastapi.params import Depends

from app.deps.repository import (
    get_attribute_repository,
    get_amenity_repository,
    get_room_type_repository,
    get_country_repository, 
    get_setting_repository,
    get_token_repository, 
    get_user_repository,
    get_city_repository,
    get_location_repository,
)

from app.repositories.country_repository import CountryRepository
from app.repositories.setting_repository import SettingRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.services import token_service
from app.services import user_service
from app.services.country_service import CountryService
from app.services.ip_service import IpService
from app.services.login_log_service import LoginLogService
from app.services.setting_service import SettingService
from app.services.storage_service import StorageService
from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.services.location_service import LocationService
from app.services.city_service import CityService
from app.services.country_service import CountryService

# Dependency injection function to provide an instance of UserService with the required UserRepository dependency.
async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    
    # Return an instance of UserService, initialized with the provided UserRepository.
    return UserService(user_repository) 

# Dependency injection function to provide an instance of TokenService with the required TokenRepository dependency.    
async def get_token_service(
    token_repository: TokenRepository = Depends(get_token_repository),
) -> TokenService:
    # Return an instance of TokenService, initialized with the provided TokenRepository.
    return TokenService(token_repository)

async def get_login_log_service(
    login_log_repository: TokenRepository = Depends(get_token_repository),
):
    # Return an instance of LoginLogService, initialized with the provided UserService and TokenService.
    return LoginLogService(login_log_repository)

# Dependency injection function to provide an instance of IpService.
async def get_ip_service():
    """Get the IP service."""
    return IpService()


async def get_setting_service(
    setting_repository: SettingRepository = Depends(get_setting_repository),
) -> SettingService:
    return SettingService(setting_repository)


def get_storage_service():
    """Get the storage service."""
    return StorageService()

async def get_country_service(
    country_repository: CountryRepository = Depends(get_country_repository),
) -> CountryService:
    return CountryService(country_repository)

async def get_city_service(
    city_repository: CityRepository = Depends(get_city_repository),
) -> CityService:
    return CityService(city_repository)

async def get_location_service(
    location_repository: LocationRepository = Depends(get_location_repository),
) -> LocationService:
    return LocationService(location_repository)


async def get_facility_service(
    facility_repository: FacilityRepository = Depends(get_attribute_repository),
) -> FacilityService:
    return FacilityService(facility_repository)


async def get_amenity_service(
    amenity_repository: AmenityRepository = Depends(get_amenity_repository),
) -> AmenityService:
    return AmenityService(amenity_repository)


async def get_room_type_service(
    room_type_repository: RoomTypeRepository = Depends(get_room_type_repository),
) -> RoomTypeService:
    return RoomTypeService(room_type_repository)
