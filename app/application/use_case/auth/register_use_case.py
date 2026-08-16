from uvicorn import logging

from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.events.events.users.create_user_event import CreateUserEvent
from app.models.user_model import User, UserStatus, UserRole
from app.services.user_service import UserService
from app.application.dto.auth import RegisterDTO
from app.core.events import EventBus

class RegisterUseCase:
    def __init__(
        self,
        user_service: UserService,
        event_bus: EventBus,
        verify_csrf: bool,
    ):
        self.user_service = user_service
        self.password_hasher = PasswordHasher()
        self.verify_csrf = verify_csrf
        self.event_bus = event_bus
    async def execute(self, data: RegisterDTO):
        if await self.user_service.get_user_by_email(data.email):
            raise AppException(
                status_code=409,
                message="Email already exists",
                error_code="EMAIL_ALREADY_EXISTS",
                field="email",
            )
        if await self.user_service.get_user_by_phone(data.phone):
            raise AppException(
                status_code=409,
                message="Phone number already exists",
                error_code="PHONE_ALREADY_EXISTS",
                field="phone",
            )

       
        payload = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password= await self.password_hasher.hash_password(data.password),  # Hash the password before storing
            role=UserRole.USER,  # Assuming you have a UserStatus enum for roles
            status=UserStatus.INACTIVE,  # Assuming you have a UserStatus enum for status
            is_subscribed = data.is_subscriber,
            is_terms_accepted=data.is_terms_accept
        )

        user = await self.user_service.create_user(payload)

        try:
            await self.event_bus.publish(CreateUserEvent(user))
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.warning("Failed to publish CreateUserEvent for user %s: %s", user.id, exc)

        return user
