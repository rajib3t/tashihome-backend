from datetime import datetime, timezone
import logging

from app.application.dto.host_requests.host_request import ConvertHostRequestDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.events import EventBus
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.deps.auth import CurrentUser
from app.events.events.users.create_vendor_event import CreateVendorEvent
from app.models.address_model import Address
from app.models.company_model import Company
from app.models.host_request_message_model import HostRequestMessage
from app.models.host_request_model import HostRequestStatus
from app.models.user_model import User, UserRole, UserStatus
from app.schemas.vendor_schema import VendorUserResponseData
from app.services.address_service import AddressService
from app.services.company_service import CompanyService
from app.services.host_request_service import HostRequestService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class ConvertHostRequestUseCase(BaseUseCase):
    def __init__(
        self,
        host_request_service: HostRequestService,
        user_service: UserService,
        company_service: CompanyService,
        address_service: AddressService,
        event_bus: EventBus,
        current_user: CurrentUser,
    ):
        self.host_request_service = host_request_service
        self.user_service = user_service
        self.company_service = company_service
        self.address_service = address_service
        self.event_bus = event_bus
        self.current_user = current_user
        self.password_hasher = PasswordHasher()

    async def execute(
        self,
        request_id: str,
        data: ConvertHostRequestDTO,
    ) -> VendorUserResponseData:
        # Use the shared session from any injected service (all share the same one)
        session = self.user_service.user_repository.db

        host_request = await self.host_request_service.get_by_public_id(
            public_id=request_id,
            with_messages=True,
            flush=False,
        )
        if not host_request:
            raise AppException(
                status_code=404,
                message="Host request not found",
                error_code="HOST_REQUEST_NOT_FOUND",
                field="request_id",
            )

        if host_request.status == HostRequestStatus.CONVERTED:
            raise AppException(
                status_code=400,
                message="This host application has already been converted.",
                error_code="APPLICATION_ALREADY_CONVERTED",
                field="request_id",
            )

        # ── 1. Resolve or create User ────────────────────────────────────────
        user: User | None = None

        if host_request.user_id:
            user = await self.user_service.get_user_by_id(
                host_request.user_id,
                with_relations={"company": True},
                flush=False,
            )

        if user is None:
            user = await self.user_service.get_user_by_email(
                host_request.email,
                with_relations={"company": True},
                flush=False,
            )

        if user is not None:
            user.role = UserRole.VENDOR
            user.status = UserStatus.ACTIVE
            session.add(user)
            await session.flush()
        else:
            raw_password = data.temporary_password if data.temporary_password else host_request.phone
            hashed_password = await self.password_hasher.hash_password(raw_password)
            user = User(
                full_name=host_request.full_name,
                email=host_request.email,
                phone=host_request.phone,
                password=hashed_password,
                role=UserRole.VENDOR,
                status=UserStatus.ACTIVE,
            )
            session.add(user)
            await session.flush()

        # ── 2. Resolve or create Company ─────────────────────────────────────
        company_name = (
            data.company_name
            or host_request.company_name
            or host_request.property_name
            or f"{user.full_name or 'Host'}'s Properties"
        )
        company_email = data.company_email or host_request.email
        company_phone = data.company_phone or host_request.phone

        # Fetch via explicit query – no lazy attribute access
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

        # ── 3. Resolve or create Address ─────────────────────────────────────
        address_line1 = data.address_line1 or host_request.address or host_request.city or "Address Line 1"
        address_line2 = data.address_line2
        postal_code = data.postal_code or "000000"
        country = data.country or "India"

        address = await self.address_service.get_company_address_by_owner_id(
            owner_id=company.id,
            flush=False,
        )
        if address is None:
            address = Address(
                address_line1=address_line1,
                address_line2=address_line2,
                postal_code=postal_code,
                country=country,
                owner_id=company.id,
                owner_type="company",
            )
            session.add(address)
        else:
            address.address_line1 = address_line1
            if address_line2 is not None:
                address.address_line2 = address_line2
            address.postal_code = postal_code
            address.country = country
            session.add(address)

        # ── 4. Update HostRequest ─────────────────────────────────────────────
        host_request.status = HostRequestStatus.CONVERTED
        host_request.converted_user_id = user.id
        host_request.reviewed_by = self.current_user.id
        host_request.reviewed_at = datetime.now(timezone.utc)
        session.add(host_request)

        # Fetch admin name via explicit query
        admin_user = await self.user_service.get_user_by_id(self.current_user.id)
        admin_name = admin_user.full_name if admin_user and admin_user.full_name else "Administrator"

        conversion_msg = HostRequestMessage(
            host_request_id=host_request.id,
            sender_id=self.current_user.id,
            sender_name=admin_name,
            sender_role="admin",
            message=f"[Application Approved & Converted] User converted to Host (Vendor ID: {user.public_id}).",
            is_internal=True,
        )
        session.add(conversion_msg)

        # Final flush – outer get_db() dependency handles the commit
        await session.flush()

        # ── 5. Dispatch event (best-effort, after flush) ──────────────────────
        try:
            await self.event_bus.publish(
                CreateVendorEvent(
                    # Pass a plain dict so the event doesn't touch the ORM user object
                    type("_U", (), {
                        "id": user.id,
                        "public_id": user.public_id,
                        "full_name": user.full_name,
                        "email": user.email,
                        "phone": user.phone,
                    })()
                )
            )
        except Exception as exc:
            logger.warning("Failed to publish CreateVendorEvent for user %s: %s", user.id, exc)

        # ── 6. Build response from fresh query ────────────────────────────────
        refreshed_user = await self.user_service.get_user_by_id(
            user.id,
            with_relations={"company": True},
            flush=True,
        )
        return await self.user_service.build_vendor_response(refreshed_user or user)
