import asyncio
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest

from app.application.dto.host_requests.host_request import BecomeHostDTO
from app.application.dto.vendors.vendor import AdminConvertUserToHostDTO, AdminOnboardHostDTO
from app.application.use_case.admin.vendors.convert_user_use_case import ConvertUserToVendorUseCase
from app.application.use_case.admin.vendors.onboard_host_use_case import AdminOnboardHostUseCase
from app.application.use_case.user.become_host_use_case import BecomeHostUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import User, UserRole, UserStatus
from app.schemas.vendor_schema import VendorUserResponseData


def test_admin_onboard_host_success():
    async def run_test():
        created_user = MagicMock(
            id=15,
            public_id=uuid.uuid4(),
            email="directhost@example.com",
            full_name="Direct Host",
            phone="9123456780",
            role=UserRole.VENDOR,
            status=UserStatus.ACTIVE,
            company=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_email.return_value = None
        user_service.get_user_by_phone.return_value = None
        user_service.create_user.return_value = created_user
        user_service.get_user_by_id.return_value = created_user
        user_service.user_repository = MagicMock()
        user_service.user_repository.db = MagicMock()
        user_service.user_repository.db.in_transaction.return_value = False
        user_service.user_repository.db.flush = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aenter__ = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        user_service.build_vendor_response = AsyncMock(
            return_value=VendorUserResponseData(
                id=str(created_user.public_id),
                email=created_user.email,
                full_name=created_user.full_name,
                phone=created_user.phone,
                status="active",
                role=UserRole.VENDOR,
            )
        )

        company_service = AsyncMock()
        company_service.create.return_value = MagicMock(id=55)

        address_service = AsyncMock()
        address_service.create.return_value = MagicMock(id=88)

        event_bus = AsyncMock()
        current_user = CurrentUser(id=1, role="admin")

        use_case = AdminOnboardHostUseCase(
            user_service=user_service,
            company_service=company_service,
            address_service=address_service,
            event_bus=event_bus,
            current_user=current_user,
        )

        dto = AdminOnboardHostDTO(
            full_name="Direct Host",
            email="directhost@example.com",
            phone="9123456780",
            company_name="Direct Homestay",
            address_line1="123 Ridge Road",
            postal_code="737101",
            country="India",
        )

        result = await use_case.execute(dto)

        assert result.email == "directhost@example.com"
        assert result.role == UserRole.VENDOR
        user_service.create_user.assert_awaited_once()
        company_service.create.assert_awaited_once()
        address_service.create.assert_awaited_once()
        event_bus.publish.assert_awaited_once()

    asyncio.run(run_test())


def test_admin_convert_user_to_host_success():
    async def run_test():
        user_pub_id = str(uuid.uuid4())
        existing_user = MagicMock(
            id=20,
            public_id=user_pub_id,
            email="regularguest@example.com",
            full_name="Regular Guest",
            phone="9876543210",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            company=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = existing_user
        user_service.get_user_by_id.return_value = existing_user
        user_service.update.return_value = existing_user
        user_service.user_repository = MagicMock()
        user_service.user_repository.db = MagicMock()
        user_service.user_repository.db.in_transaction.return_value = False
        user_service.user_repository.db.flush = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aenter__ = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        user_service.build_vendor_response = AsyncMock(
            return_value=VendorUserResponseData(
                id=user_pub_id,
                email=existing_user.email,
                full_name=existing_user.full_name,
                phone=existing_user.phone,
                status="active",
                role=UserRole.VENDOR,
            )
        )

        company_service = AsyncMock()
        company_service.create.return_value = MagicMock(id=66)

        address_service = AsyncMock()
        address_service.get_company_address_by_owner_id.return_value = None
        address_service.create.return_value = MagicMock(id=99)

        event_bus = AsyncMock()
        current_user = CurrentUser(id=1, role="admin")

        use_case = ConvertUserToVendorUseCase(
            user_service=user_service,
            company_service=company_service,
            address_service=address_service,
            event_bus=event_bus,
            current_user=current_user,
        )

        dto = AdminConvertUserToHostDTO(
            company_name="Guest Upgraded Homestay",
            address_line1="Mall Road",
            postal_code="734101",
            country="India",
        )

        result = await use_case.execute(user_pub_id, dto)

        assert result.role == UserRole.VENDOR
        assert existing_user.role == UserRole.VENDOR
        company_service.create.assert_awaited_once()
        event_bus.publish.assert_awaited_once()

    asyncio.run(run_test())


def test_admin_convert_user_already_vendor_raises_400():
    async def run_test():
        user_pub_id = str(uuid.uuid4())
        already_vendor = MagicMock(
            id=20,
            public_id=user_pub_id,
            role=UserRole.VENDOR,
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = already_vendor

        use_case = ConvertUserToVendorUseCase(
            user_service=user_service,
            company_service=AsyncMock(),
            address_service=AsyncMock(),
            event_bus=AsyncMock(),
            current_user=CurrentUser(id=1, role="admin"),
        )

        with pytest.raises(AppException) as exc:
            await use_case.execute(user_pub_id, AdminConvertUserToHostDTO())
        assert exc.value.status_code == 400
        assert exc.value.error_code == "USER_ALREADY_VENDOR"

    asyncio.run(run_test())


def test_user_become_host_success():
    async def run_test():
        existing_user = MagicMock(
            id=33,
            public_id=uuid.uuid4(),
            email="me@example.com",
            full_name="Me",
            phone="9876543210",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            company=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_id.return_value = existing_user
        user_service.update.return_value = existing_user
        user_service.user_repository = MagicMock()
        user_service.user_repository.db = MagicMock()
        user_service.user_repository.db.in_transaction.return_value = False
        user_service.user_repository.db.flush = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aenter__ = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        user_service.build_vendor_response = AsyncMock(
            return_value=VendorUserResponseData(
                id=str(existing_user.public_id),
                email=existing_user.email,
                full_name=existing_user.full_name,
                phone=existing_user.phone,
                status="active",
                role=UserRole.VENDOR,
            )
        )

        company_service = AsyncMock()
        company_service.create.return_value = MagicMock(id=77)

        address_service = AsyncMock()
        address_service.get_company_address_by_owner_id.return_value = None
        address_service.create.return_value = MagicMock(id=88)

        event_bus = AsyncMock()
        current_user = CurrentUser(id=33, role="user")

        use_case = BecomeHostUseCase(
            user_service=user_service,
            company_service=company_service,
            address_service=address_service,
            event_bus=event_bus,
            current_user=current_user,
        )

        dto = BecomeHostDTO(
            company_name="My Mountain Villa",
            address_line1="Hill Cart Road",
            postal_code="734001",
            country="India",
        )

        result = await use_case.execute(dto)

        assert result.role == UserRole.VENDOR
        assert existing_user.role == UserRole.VENDOR
        company_service.create.assert_awaited_once()
        event_bus.publish.assert_awaited_once()

    asyncio.run(run_test())

