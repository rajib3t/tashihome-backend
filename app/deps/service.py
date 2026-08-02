
from app.services.email_template_service import EmailTemplateService
from app.services.email_service import BrevoEmailService
from app.services.email_service import MailgunEmailService
from app.services.email_service import SMTPEmailService
from app.services.email_service import MockEmailService
from app.core.config import settings
from app.services.email_service import BaseEmailService
from app.repositories.facility_repository import  FacilityRepository
from app.repositories.amenity_repository import AmenityRepository
from app.repositories.room_type_repository import RoomTypeRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.address_repository import AddressRepository
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
    get_company_repository,
    get_address_repository,
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
from app.services.company_service import CompanyService
from app.services.address_service import AddressService

# Dependency injection function to provide an instance of UserService with the required UserRepository dependency.
async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    company_repository: CompanyRepository = Depends(get_company_repository),
    address_repository: AddressRepository = Depends(get_address_repository),
) -> UserService:
    
    # Return an instance of UserService, initialized with the provided UserRepository.
    return UserService(
        user_repository,
        CompanyService(company_repository),
        AddressService(address_repository),
    ) 

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


async def get_email_service() -> BaseEmailService:
    provider = (settings.EMAIL_PROVIDER or "mock").lower()
    if provider == "smtp":
        if not settings.SMTP_HOST:
            return MockEmailService(settings.EMAILS_FROM_EMAIL, settings.EMAILS_FROM_NAME)
        return SMTPEmailService(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
            settings.EMAILS_FROM_EMAIL,
            settings.EMAILS_FROM_NAME,
        )
    if provider == "mailgun" and settings.MAILGUN_DOMAIN and settings.MAILGUN_API_KEY:
        return MailgunEmailService(
            settings.MAILGUN_DOMAIN,
            settings.MAILGUN_API_KEY,
            settings.EMAILS_FROM_EMAIL,
            settings.EMAILS_FROM_NAME,
        )
    if provider == "brevo" and settings.BREVO_API_KEY:
        return BrevoEmailService(
            settings.BREVO_API_KEY,
            settings.EMAILS_FROM_EMAIL,
            settings.EMAILS_FROM_NAME,
        )
    return MockEmailService(settings.EMAILS_FROM_EMAIL, settings.EMAILS_FROM_NAME)


async def get_email_template_service() -> EmailTemplateService:
    return EmailTemplateService()
