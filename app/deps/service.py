
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
from app.repositories.property_repository import PropertyRepository
from app.repositories.property_asset_repository import PropertyAssetRepository
from app.repositories.property_room_type_repository import PropertyRoomTypeRepository
from app.repositories.property_room_type_price_repository import PropertyRoomTypePriceRepository
from app.repositories.property_facility_repository import PropertyFacilityRepository
from app.repositories.property_amenity_repository import PropertyAmenityRepository
from app.repositories.property_food_option_repository import PropertyFoodOptionRepository
from app.services.facility_service import  FacilityService
from app.services.amenity_service import AmenityService
from app.services.room_type_service import RoomTypeService
from app.services.city_service import CityService
from app.repositories.city_repository import CityRepository
from fastapi.params import Depends

from app.deps.repository import (
    get_attribute_repository,
    get_amenity_repository,
    get_property_room_type_repository,
    get_property_room_type_price_repository,
    get_room_type_repository,
    get_country_repository, 
    get_setting_repository,
    get_token_repository, 
    get_user_repository,
    get_city_repository,
    get_location_repository,
    get_company_repository,
    get_address_repository,
    get_property_repository,
    get_property_asset_repository,
    get_property_facility_repository,
    get_property_amenity_repository,
    get_property_food_option_repository,
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
from app.services.property_service import PropertyService
from app.services.property_asset_service import PropertyAssetService
from app.services.property_room_type_service import PropertyRoomTypeService
from app.services.property_room_type_price_service import PropertyRoomTypePriceService
from app.services.property_facility_service import PropertyFacilityService
from app.services.property_amenity_service import PropertyAmenityService
from app.services.property_food_option_service import PropertyFoodOptionService

async def get_company_service(
    company_repository: CompanyRepository = Depends(get_company_repository),
) -> CompanyService:
    return CompanyService(company_repository)


async def get_address_service(
    address_repository: AddressRepository = Depends(get_address_repository),
) -> AddressService:
    return AddressService(address_repository)


# Dependency injection function to provide an instance of UserService with the required UserRepository dependency.
async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    company_service: CompanyService = Depends(get_company_service),
    address_service: AddressService = Depends(get_address_service),
) -> UserService:
    return UserService(
        user_repository,
        company_service,
        address_service,
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


async def get_property_service(
    property_repository: PropertyRepository = Depends(get_property_repository),
) -> PropertyService:
    return PropertyService(property_repository)


async def get_property_asset_service(
    property_asset_repository: PropertyAssetRepository = Depends(get_property_asset_repository),
) -> PropertyAssetService:
    return PropertyAssetService(property_asset_repository)


async def get_property_room_type_service(
    property_room_type_repository: PropertyRoomTypeRepository = Depends(get_property_room_type_repository),
) -> PropertyRoomTypeService:
    return PropertyRoomTypeService(property_room_type_repository)


async def get_property_room_type_price_service(
    property_room_type_price_repository: PropertyRoomTypePriceRepository = Depends(get_property_room_type_price_repository),
) -> PropertyRoomTypePriceService:
    return PropertyRoomTypePriceService(property_room_type_price_repository)


async def get_property_facility_service(
    property_facility_repository: PropertyFacilityRepository = Depends(get_property_facility_repository),
) -> PropertyFacilityService:
    return PropertyFacilityService(property_facility_repository)


async def get_property_amenity_service(
    property_amenity_repository: PropertyAmenityRepository = Depends(get_property_amenity_repository),
) -> PropertyAmenityService:
    return PropertyAmenityService(property_amenity_repository)


async def get_property_food_option_service(
    property_food_option_repository: PropertyFoodOptionRepository = Depends(get_property_food_option_repository),
) -> PropertyFoodOptionService:
    return PropertyFoodOptionService(property_food_option_repository)


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


from app.deps.repository import (
    get_booking_repository,
    get_payment_repository,
    get_refund_request_repository,
    get_room_block_repository,
)
from app.repositories.booking_repository import BookingRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.refund_request_repository import RefundRequestRepository
from app.repositories.room_block_repository import RoomBlockRepository
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.refund_request_service import RefundRequestService


async def get_booking_service(
    booking_repository: BookingRepository = Depends(get_booking_repository),
    property_repository: PropertyRepository = Depends(get_property_repository),
    property_room_type_repository: PropertyRoomTypeRepository = Depends(get_property_room_type_repository),
    room_block_repository: RoomBlockRepository = Depends(get_room_block_repository),
    refund_request_repository: RefundRequestRepository = Depends(get_refund_request_repository),
) -> BookingService:
    return BookingService(
        booking_repository=booking_repository,
        property_repository=property_repository,
        property_room_type_repository=property_room_type_repository,
        room_block_repository=room_block_repository,
        refund_request_repository=refund_request_repository,
    )


async def get_payment_service(
    payment_repository: PaymentRepository = Depends(get_payment_repository),
) -> PaymentService:
    return PaymentService(payment_repository)


from app.services.room_block_service import RoomBlockService


async def get_room_block_service(
    room_block_repository: RoomBlockRepository = Depends(get_room_block_repository),
    property_repository: PropertyRepository = Depends(get_property_repository),
    property_room_type_repository: PropertyRoomTypeRepository = Depends(get_property_room_type_repository),
    booking_repository: BookingRepository = Depends(get_booking_repository),
) -> RoomBlockService:
    return RoomBlockService(
        room_block_repository=room_block_repository,
        property_repository=property_repository,
        property_room_type_repository=property_room_type_repository,
        booking_repository=booking_repository,
    )


async def get_refund_request_service(
    refund_request_repository: RefundRequestRepository = Depends(get_refund_request_repository),
) -> RefundRequestService:
    return RefundRequestService(refund_request_repository)


from app.services.razorpay_service import RazorpayService


async def get_razorpay_service() -> RazorpayService:
    return RazorpayService()


async def get_email_template_service() -> EmailTemplateService:
    return EmailTemplateService()


from app.deps.repository import (
    get_dashboard_repository,
    get_payout_repository,
    get_vendor_bank_account_repository,
    get_vendor_razorpay_contact_repository,
    get_vendor_razorpay_fund_account_repository,
)
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.payout_repository import PayoutRepository
from app.repositories.vendor_bank_account_repository import VendorBankAccountRepository
from app.repositories.vendor_razorpay_contact_repository import VendorRazorpayContactRepository
from app.repositories.vendor_razorpay_fund_account_repository import VendorRazorpayFundAccountRepository
from app.services.dashboard_service import DashboardService
from app.services.payout_service import PayoutService
from app.services.vendor_bank_account_service import VendorBankAccountService
from app.services.vendor_razorpay_contact_service import VendorRazorpayContactService
from app.services.vendor_razorpay_fund_account_service import VendorRazorpayFundAccountService


async def get_dashboard_service(
    dashboard_repository: DashboardRepository = Depends(get_dashboard_repository),
) -> DashboardService:
    return DashboardService(dashboard_repository)


async def get_payout_service(
    payout_repository: PayoutRepository = Depends(get_payout_repository),
) -> PayoutService:
    return PayoutService(payout_repository)


async def get_vendor_bank_account_service(
    vendor_bank_account_repository: VendorBankAccountRepository = Depends(get_vendor_bank_account_repository),
) -> VendorBankAccountService:
    return VendorBankAccountService(vendor_bank_account_repository)


async def get_vendor_razorpay_contact_service(
    vendor_razorpay_contact_repository: VendorRazorpayContactRepository = Depends(get_vendor_razorpay_contact_repository),
) -> VendorRazorpayContactService:
    return VendorRazorpayContactService(vendor_razorpay_contact_repository)


async def get_vendor_razorpay_fund_account_service(
    vendor_razorpay_fund_account_repository: VendorRazorpayFundAccountRepository = Depends(get_vendor_razorpay_fund_account_repository),
) -> VendorRazorpayFundAccountService:
    return VendorRazorpayFundAccountService(vendor_razorpay_fund_account_repository)



from app.deps.repository import get_review_repository, get_testimonial_repository
from app.repositories.review_repository import ReviewRepository
from app.repositories.testimonial_repository import TestimonialRepository
from app.services.review_service import ReviewService
from app.services.testimonial_service import TestimonialService


async def get_review_service(
    review_repository: ReviewRepository = Depends(get_review_repository),
) -> ReviewService:
    return ReviewService(review_repository)


async def get_testimonial_service(
    testimonial_repository: TestimonialRepository = Depends(get_testimonial_repository),
) -> TestimonialService:
    return TestimonialService(testimonial_repository)


