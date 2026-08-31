import logging

from app.application.dto.host_requests.host_request import BecomeHostDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.events import EventBus
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.events.events.users.create_vendor_event import CreateVendorEvent
from app.models.address_model import Address
from app.models.company_model import Company
from app.models.user_model import UserRole, UserStatus
from app.schemas.vendor_schema import VendorUserResponseData
from app.services.address_service import AddressService
from app.services.company_service import CompanyService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class BecomeHostUseCase(BaseUseCase):
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

    async def execute(self, data: BecomeHostDTO) -> VendorUserResponseData:
        user = await self.user_service.get_user_by_id(
            self.current_user.id,
            with_relations={"company": True},
            flush=True,
        )
        if not user:
            raise AppException(
                status_code=404,
                message="User not found",
                error_code="USER_NOT_FOUND",
            )

        if user.role == UserRole.VENDOR:
            raise AppException(
                status_code=400,
                message="You are already registered as a host.",
                error_code="ALREADY_A_HOST",
            )

        session = self.user_service.user_repository.db

        # 1. Elevate role
        user.role = UserRole.VENDOR
        user.status = UserStatus.ACTIVE
        if data.full_name and data.full_name.strip():
            user.full_name = data.full_name.strip()
        if data.phone and data.phone.strip():
            user.phone = data.phone.strip()
        session.add(user)
        await session.flush()

        company_name = data.company_name.strip()
        company_email = data.company_email.strip().lower() if data.company_email else user.email
        company_phone = data.company_phone.strip() if data.company_phone else user.phone

        # 2. Resolve or create company – explicit query to avoid lazy-load
        company = await self.company_service.company_repository.get_company_by_user_id(
            user_id=user.id,
            flush=False,
        )
        if company is None:
            company = Company(
                name=company_name,
                email=company_email,
                phone=company_phone,
                user_id=user.id,
            )
            session.add(company)
            await session.flush()
        else:
            company.name = company_name
            company.email = company_email
            company.phone = company_phone
            session.add(company)
            await session.flush()

        # 3. Resolve or create address
        address = await self.address_service.get_company_address_by_owner_id(
            owner_id=company.id,
            flush=False,
        )
        if address is None:
            address = Address(
                address_line1=data.address_line1.strip(),
                address_line2=data.address_line2.strip() if data.address_line2 else None,
                postal_code=data.postal_code.strip(),
                country=data.country.strip(),
                owner_id=company.id,
                owner_type="company",
            )
            session.add(address)
        else:
            address.address_line1 = data.address_line1.strip()
            address.address_line2 = data.address_line2.strip() if data.address_line2 else None
            address.postal_code = data.postal_code.strip()
            address.country = data.country.strip()
            session.add(address)

        await session.flush()

        # 4. Publish event (best-effort)
        try:
            await self.event_bus.publish(CreateVendorEvent(user))
        except Exception as exc:
            logger.warning("Failed to publish CreateVendorEvent for user %s: %s", user.id, exc)

        refreshed = await self.user_service.get_user_by_id(
            user.id,
            with_relations={"company": True},
            flush=True,
        )
        return await self.user_service.build_vendor_response(refreshed or user)
