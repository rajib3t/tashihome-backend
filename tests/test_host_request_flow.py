import asyncio
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest

from app.application.dto.host_requests.host_request import (
    AddHostRequestMessageDTO,
    ConvertHostRequestDTO,
    CreateHostRequestDTO,
    HostRequestQueryDTO,
    UpdateHostRequestStatusDTO,
)
from app.application.use_case.admin.host_requests.add_host_request_message_use_case import (
    AddHostRequestMessageUseCase,
)
from app.application.use_case.admin.host_requests.convert_host_request_use_case import (
    ConvertHostRequestUseCase,
)
from app.application.use_case.admin.host_requests.get_host_request_use_case import (
    GetHostRequestUseCase,
)
from app.application.use_case.admin.host_requests.list_host_requests_use_case import (
    ListHostRequestsUseCase,
)
from app.application.use_case.admin.host_requests.update_host_request_status_use_case import (
    UpdateHostRequestStatusUseCase,
)
from app.application.use_case.public.host_request.submit_host_request_use_case import (
    SubmitHostRequestUseCase,
)
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.host_request_model import HostRequest, HostRequestStatus
from app.models.user_model import User, UserRole, UserStatus
from app.repositories.base_repository import Page
from app.schemas.host_request_schema import HostRequestResponseData
from app.schemas.vendor_schema import VendorUserResponseData


def test_submit_host_request_success():
    async def run_test():
        host_request_service = AsyncMock()
        host_request_service.get_pending_or_review_by_email.return_value = None
        host_request_service.host_request_repository = MagicMock()
        host_request_service.host_request_repository.db = MagicMock()
        host_request_service.host_request_repository.db.in_transaction.return_value = False
        host_request_service.host_request_repository.db.flush = AsyncMock()
        host_request_service.host_request_repository.db.begin.return_value.__aenter__ = AsyncMock()
        host_request_service.host_request_repository.db.begin.return_value.__aexit__ = AsyncMock(return_value=None)

        created_mock = MagicMock(
            id=1,
            public_id=uuid.uuid4(),
            full_name="John Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="John Homestay",
            property_name="Sunny Villa",
            property_type="homestay",
            city="Gangtok",
            address="MG Marg",
            expected_rooms=5,
            notes="Excited to host!",
            status=HostRequestStatus.PENDING,
            user_id=None,
            reviewed_by=None,
            reviewed_at=None,
            converted_user_id=None,
            created_at=None,
            updated_at=None,
            messages=[],
        )
        host_request_service.create.return_value = created_mock
        host_request_service.get_by_id.return_value = created_mock
        host_request_service.build_host_request_response = MagicMock(
            return_value=HostRequestResponseData(
                id=str(created_mock.public_id),
                full_name="John Doe",
                email="john@example.com",
                phone="1234567890",
                status=HostRequestStatus.PENDING,
            )
        )

        user_service = AsyncMock()
        user_service.get_user_by_email.return_value = None

        use_case = SubmitHostRequestUseCase(
            host_request_service=host_request_service,
            user_service=user_service,
        )

        dto = CreateHostRequestDTO(
            full_name="John Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="John Homestay",
            property_name="Sunny Villa",
            property_type="homestay",
            city="Gangtok",
            address="MG Marg",
            expected_rooms=5,
            notes="Excited to host!",
        )

        result = await use_case.execute(dto)
        assert result.email == "john@example.com"
        assert result.status == HostRequestStatus.PENDING
        host_request_service.create.assert_awaited_once()

    asyncio.run(run_test())


def test_submit_host_request_duplicate_pending_raises_409():
    async def run_test():
        host_request_service = AsyncMock()
        host_request_service.get_pending_or_review_by_email.return_value = MagicMock(id=1)

        user_service = AsyncMock()

        use_case = SubmitHostRequestUseCase(
            host_request_service=host_request_service,
            user_service=user_service,
        )

        dto = CreateHostRequestDTO(
            full_name="John Doe",
            email="john@example.com",
            phone="1234567890",
        )

        with pytest.raises(AppException) as exc:
            await use_case.execute(dto)
        assert exc.value.status_code == 409
        assert exc.value.error_code == "PENDING_REQUEST_EXISTS"

    asyncio.run(run_test())


def test_submit_host_request_already_vendor_raises_400():
    async def run_test():
        host_request_service = AsyncMock()
        host_request_service.get_pending_or_review_by_email.return_value = None

        user_service = AsyncMock()
        existing_vendor = MagicMock(id=10, role=UserRole.VENDOR)
        user_service.get_user_by_email.return_value = existing_vendor

        use_case = SubmitHostRequestUseCase(
            host_request_service=host_request_service,
            user_service=user_service,
        )

        dto = CreateHostRequestDTO(
            full_name="John Doe",
            email="john@example.com",
            phone="1234567890",
        )

        with pytest.raises(AppException) as exc:
            await use_case.execute(dto)
        assert exc.value.status_code == 400
        assert exc.value.error_code == "ALREADY_A_HOST"

    asyncio.run(run_test())


def test_list_host_requests_success():
    async def run_test():
        host_request_service = AsyncMock()
        mock_req = MagicMock(
            public_id=uuid.uuid4(),
            full_name="Jane",
            email="jane@example.com",
            phone="9998887776",
            status=HostRequestStatus.PENDING,
        )
        host_request_service.list.return_value = Page(
            items=[mock_req],
            total=1,
            page=1,
            page_size=10,
        )
        host_request_service.build_host_request_response = MagicMock(
            return_value=HostRequestResponseData(
                id=str(mock_req.public_id),
                full_name="Jane",
                email="jane@example.com",
                phone="9998887776",
                status=HostRequestStatus.PENDING,
            )
        )

        current_user = CurrentUser(id=1, role="admin")
        use_case = ListHostRequestsUseCase(
            host_request_service=host_request_service,
            current_user=current_user,
        )

        query = HostRequestQueryDTO(page=1, size=10, status="pending")
        result = await use_case.execute(query)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].email == "jane@example.com"

    asyncio.run(run_test())


def test_update_host_request_status_success():
    async def run_test():
        host_request = MagicMock(
            id=5,
            public_id=uuid.uuid4(),
            status=HostRequestStatus.PENDING,
        )
        host_request_service = AsyncMock()
        host_request_service.get_by_public_id.return_value = host_request
        host_request_service.get_by_id.return_value = host_request
        host_request_service.update.return_value = host_request
        host_request_service.host_request_repository = MagicMock()
        host_request_service.host_request_repository.db = MagicMock()
        host_request_service.host_request_repository.db.in_transaction.return_value = False
        host_request_service.host_request_repository.db.flush = AsyncMock()
        host_request_service.host_request_repository.db.begin.return_value.__aenter__ = AsyncMock()
        host_request_service.host_request_repository.db.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        host_request_service.build_host_request_response = MagicMock(
            return_value=HostRequestResponseData(
                id=str(host_request.public_id),
                full_name="Jane",
                email="jane@example.com",
                phone="9998887776",
                status=HostRequestStatus.UNDER_REVIEW,
            )
        )

        user_service = AsyncMock()
        user_service.get_user_by_id.return_value = MagicMock(full_name="Admin Boss")

        current_user = CurrentUser(id=1, role="admin")
        use_case = UpdateHostRequestStatusUseCase(
            host_request_service=host_request_service,
            user_service=user_service,
            current_user=current_user,
        )

        dto = UpdateHostRequestStatusDTO(status="under_review", notes="Checking identity documents")
        result = await use_case.execute(str(host_request.public_id), dto)

        assert result.status == HostRequestStatus.UNDER_REVIEW
        assert host_request.status == HostRequestStatus.UNDER_REVIEW

    asyncio.run(run_test())


def test_add_host_request_message_success():
    async def run_test():
        host_request = MagicMock(
            id=5,
            public_id=uuid.uuid4(),
            status=HostRequestStatus.UNDER_REVIEW,
        )
        host_request_service = AsyncMock()
        host_request_service.get_by_public_id.return_value = host_request
        host_request_service.get_by_id.return_value = host_request
        host_request_service.host_request_repository = MagicMock()
        host_request_service.host_request_repository.db = MagicMock()
        host_request_service.host_request_repository.db.in_transaction.return_value = False
        host_request_service.host_request_repository.db.flush = AsyncMock()
        host_request_service.host_request_repository.db.begin.return_value.__aenter__ = AsyncMock()
        host_request_service.host_request_repository.db.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        host_request_service.build_host_request_response = MagicMock(
            return_value=HostRequestResponseData(
                id=str(host_request.public_id),
                full_name="Jane",
                email="jane@example.com",
                phone="9998887776",
                status=HostRequestStatus.UNDER_REVIEW,
            )
        )

        user_service = AsyncMock()
        user_service.get_user_by_id.return_value = MagicMock(full_name="Admin Reviewer")

        current_user = CurrentUser(id=1, role="admin")
        use_case = AddHostRequestMessageUseCase(
            host_request_service=host_request_service,
            user_service=user_service,
            current_user=current_user,
        )

        dto = AddHostRequestMessageDTO(message="Please provide trade license copy.", is_internal=False)
        result = await use_case.execute(str(host_request.public_id), dto)

        assert result is not None
        host_request_service.add_message.assert_awaited_once()

    asyncio.run(run_test())


def test_convert_host_request_to_host_success():
    async def run_test():
        req_id = uuid.uuid4()
        host_request = MagicMock(
            id=9,
            public_id=req_id,
            user_id=None,
            full_name="Tashi Wang",
            email="tashi@example.com",
            phone="9876543210",
            company_name="Tashi Homestay",
            property_name="Tashi Palace",
            city="Kalimpong",
            address="Upper Cart Road",
            status=HostRequestStatus.APPROVED,
        )

        host_request_service = AsyncMock()
        host_request_service.get_by_public_id.return_value = host_request
        host_request_service.get_by_id.return_value = host_request
        host_request_service.update.return_value = host_request

        created_user = MagicMock(
            id=42,
            public_id=uuid.uuid4(),
            email="tashi@example.com",
            full_name="Tashi Wang",
            phone="9876543210",
            role=UserRole.VENDOR,
            status=UserStatus.ACTIVE,
            company=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_id.return_value = None
        user_service.get_user_by_email.return_value = None
        user_service.create_user.return_value = created_user
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
        mock_company = MagicMock(id=101, name="Tashi Homestay")
        company_service.create.return_value = mock_company

        address_service = AsyncMock()
        address_service.get_company_address_by_owner_id.return_value = None

        event_bus = AsyncMock()
        current_user = CurrentUser(id=1, role="admin")

        use_case = ConvertHostRequestUseCase(
            host_request_service=host_request_service,
            user_service=user_service,
            company_service=company_service,
            address_service=address_service,
            event_bus=event_bus,
            current_user=current_user,
        )

        dto = ConvertHostRequestDTO(
            company_name="Tashi Homestay & Retreat",
            address_line1="Upper Cart Road",
            postal_code="734301",
            country="India",
        )

        result = await use_case.execute(str(req_id), dto)

        assert result.email == "tashi@example.com"
        assert result.role == UserRole.VENDOR
        assert host_request.status == HostRequestStatus.CONVERTED
        assert host_request.converted_user_id == 42
        event_bus.publish.assert_awaited_once()

    asyncio.run(run_test())

