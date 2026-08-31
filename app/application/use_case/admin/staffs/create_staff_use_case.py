import logging
import secrets
from app.application.dto.staffs.staff import StaffDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.events import EventBus
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.deps.auth import CurrentUser
from app.events.events.users.create_user_event import CreateUserEvent
from app.models.user_model import User, UserRole, UserStatus
from app.schemas.user_schema import UserData
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class CreateStaffUseCase(BaseUseCase):
    def __init__(
        self,
        user_service: UserService,
        event_bus: EventBus,
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.event_bus = event_bus
        self.verify_csrf = verify_csrf
        self.current_user = current_user
        self.password_hasher = PasswordHasher()

    async def execute(self, staff_dto: StaffDTO) -> UserData:
        normalized_email = staff_dto.email.strip().lower()
        if await self.user_service.get_user_by_email(normalized_email):
            raise AppException(
                status_code=409,
                message="Email already exists",
                error_code="EMAIL_ALREADY_EXISTS",
                field="email",
            )

        phone = staff_dto.phone.strip() if staff_dto.phone else None
        if phone and await self.user_service.get_user_by_phone(phone):
            raise AppException(
                status_code=409,
                message="Phone number already exists",
                error_code="PHONE_ALREADY_EXISTS",
                field="phone",
            )

        # Validate role
        role = staff_dto.role or UserRole.STAFF
        if isinstance(role, str):
            role_val = role.strip().lower()
            if role_val == "admin":
                role = UserRole.ADMIN
            elif role_val == "staff":
                role = UserRole.STAFF
            else:
                raise AppException(
                    status_code=422,
                    message="Role must be 'admin' or 'staff'.",
                    error_code="ROLE_INVALID",
                    field="role",
                )
        elif role not in (UserRole.ADMIN, UserRole.STAFF):
            raise AppException(
                status_code=422,
                message="Role must be 'admin' or 'staff'.",
                error_code="ROLE_INVALID",
                field="role",
            )

        raw_password = (
            staff_dto.password.strip()
            if staff_dto.password and staff_dto.password.strip()
            else (phone or secrets.token_urlsafe(10))
        )
        hashed_password = await self.password_hasher.hash_password(raw_password)

        payload = User(
            full_name=staff_dto.full_name.strip() if staff_dto.full_name else None,
            email=normalized_email,
            phone=phone,
            password=hashed_password,
            role=role,
            status=UserStatus.ACTIVE,
            is_subscribed=bool(staff_dto.is_subscribed),
        )

        created_user = await self.user_service.create_user(payload)

        try:
            await self.event_bus.publish(CreateUserEvent(created_user))
        except Exception as exc:
            logger.warning("Failed to publish CreateUserEvent for staff %s: %s", created_user.id, exc)

        return UserData(
            id=str(created_user.public_id),
            email=created_user.email,
            full_name=created_user.full_name or "",
            phone=created_user.phone,
            status=created_user.status.value if hasattr(created_user.status, "value") else str(created_user.status),
            role=created_user.role,
            is_profile_image_url=created_user.is_profile_image_url,
            is_subscribed=created_user.is_subscribed,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
        )

