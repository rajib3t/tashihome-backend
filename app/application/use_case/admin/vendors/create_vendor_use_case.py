from app.core.events import EventBus
from app.core.exceptions import AppException
from app.events.events.users.create_vendor_event import CreateVendorEvent
from app.application.dto.vendors.vendor import  VendorDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.models.user_model import User, UserRole, UserStatus
from app.services.user_service import UserService
from app.core.security import PasswordHasher
import logging
class CreateVendorUseCase(BaseUseCase):
    def __init__(
        self,
        user_service : UserService,
        event_bus: EventBus,
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.current_user = current_user
        self.event_bus = event_bus
        self.verify_csrf = verify_csrf
        self.passwordManager = PasswordHasher()
    async def execute(self, vendor_dto: VendorDTO) -> User:
        # Perform any necessary validation or business logic here
        if await self.user_service.get_user_by_email(vendor_dto.email):
            raise AppException(
                status_code=409,
                message="Email already exists",
                error_code="EMAIL_ALREADY_EXISTS",
                field="email",
            )
        if await self.user_service.get_user_by_phone(vendor_dto.phone):
            raise AppException(
                status_code=409,
                message="Phone number already exists",
                error_code="PHONE_ALREADY_EXISTS",
                field="phone",
            )
        payload = User(
            full_name=vendor_dto.full_name,
            email=vendor_dto.email,
            phone=vendor_dto.phone,
            password= await self.passwordManager.hash_password(vendor_dto.phone),  # Hash the password before storing
            role=UserRole.VENDOR,  # Assuming you have a UserStatus enum for roles
            status=UserStatus.INACTIVE,  # Assuming you have a UserStatus enum for status
        )

        created_vendor = await self.user_service.create_user(payload)
        try:
            await self.event_bus.publish(CreateVendorEvent(created_vendor))
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.warning("Failed to publish CreateVendorEvent for user %s: %s", created_vendor.id, exc)

        return created_vendor   