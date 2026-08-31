import logging

from app.application.dto.vendors.vendor import AdminOnboardHostDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.events import EventBus
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.deps.auth import CurrentUser
from app.events.events.users.create_vendor_event import CreateVendorEvent
from app.models.address_model import Address
from app.models.company_model import Company
from app.models.user_model import User, UserRole, UserStatus
from app.schemas.vendor_schema import VendorUserResponseData
from app.services.address_service import AddressService
from app.services.company_service import CompanyService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class AdminOnboardHostUseCase(BaseUseCase):
    def __init__(
        self,
        user_service: UserService,
        company_service: CompanyService,
        address_service: AddressService,
        event_bus: EventBus,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.company_service = company_service
        self.address_service = address_service
        self.event_bus = event_bus
        self.current_user = current_user
        self.password_hasher = PasswordHasher()

    async def execute(self, data: AdminOnboardHostDTO) -> VendorUserResponseData:
        normalized_email = data.email.strip().lower()
        normalized_phone = data.phone.strip()

        # 1. Duplicate check
        if await self.user_service.get_user_by_email(normalized_email):
            raise AppException(
                status_code=409,
                message="Email already exists",
                error_code="EMAIL_ALREADY_EXISTS",
                field="email",
            )
        if await self.user_service.get_user_by_phone(normalized_phone):
            raise AppException(
                status_code=409,
                message="Phone number already exists",
                error_code="PHONE_ALREADY_EXISTS",
                field="phone",
            )

        status_val = UserStatus.ACTIVE if (data.status or "").lower() == "active" else UserStatus.INACTIVE
        session = self.user_service.user_repository.db

        raw_password = data.password if data.password else normalized_phone
        hashed_password = await self.password_hasher.hash_password(raw_password)

        # 2. Create user
        user = User(
            full_name=data.full_name.strip(),
            email=normalized_email,
            phone=normalized_phone,
            password=hashed_password,
            role=UserRole.VENDOR,
            status=status_val,
        )
        session.add(user)
        await session.flush()

        # 3. Create company
        company_name = data.company_name or f"{user.full_name}'s Homestay"
        company_email = data.company_email or normalized_email
        company_phone = data.company_phone or normalized_phone

        company = Company(
            name=company_name,
            email=company_email,
            phone=company_phone,
            user_id=user.id,
        )
        session.add(company)
        await session.flush()

        # 4. Create address
        address = Address(
            address_line1=data.address_line1 or "Address Line 1",
            address_line2=data.address_line2,
            postal_code=data.postal_code or "000000",
            country=data.country or "India",
            owner_id=company.id,
            owner_type="company",
        )
        session.add(address)
        await session.flush()

        # 5. Publish event (best-effort)
        try:
            await self.event_bus.publish(CreateVendorEvent(user))
        except Exception as exc:
            logger.warning("Failed to publish CreateVendorEvent for user %s: %s", user.id, exc)

        # 6. Return freshly queried response
        refreshed = await self.user_service.get_user_by_id(
            user.id,
            with_relations={"company": True},
            flush=True,
        )
        return await self.user_service.build_vendor_response(refreshed or user)
