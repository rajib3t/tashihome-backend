import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.staffs.staff import (
    StaffDTO,
    StaffQueryDTO,
    StaffResetLinkDTO,
    StaffUpdateDTO,
)
from app.application.use_case.admin.staffs.create_staff_use_case import CreateStaffUseCase
from app.application.use_case.admin.staffs.get_staff_use_case import GetStaffUseCase
from app.application.use_case.admin.staffs.list_staff_use_case import ListStaffUseCase
from app.application.use_case.admin.staffs.send_password_reset_link_use_case import (
    SendStaffPasswordResetLinkUseCase,
)
from app.application.use_case.admin.staffs.update_staff_use_case import (
    UpdateStaffUseCase,
    UpdateStatusStaffUseCase,
)
from app.core.exceptions import AppException
from app.models.user_model import UserRole, UserStatus
from app.repositories.base_repository import Page


def test_list_staff_use_case():
    async def run_test():
        mock_staff = MagicMock(
            public_id=uuid.uuid4(),
            email="staff@example.com",
            full_name="Staff Member",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.STAFF,
            is_profile_image_url=None,
            is_subscribed=True,
            created_at=None,
            updated_at=None,
        )

        user_service = AsyncMock()
        user_service.list.return_value = Page(
            items=[mock_staff],
            total=1,
            page=1,
            page_size=10,
        )

        storage_service = MagicMock()
        current_user = MagicMock(role=UserRole.ADMIN)

        use_case = ListStaffUseCase(
            user_service=user_service,
            storage_service=storage_service,
            current_user=current_user,
        )

        # Default query (queries both admin and staff roles)
        params = StaffQueryDTO(page=1, size=10, email="staff@example.com", status="active")
        result = await use_case.execute(params)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].email == "staff@example.com"
        assert result.items[0].role == UserRole.STAFF
        user_service.list.assert_awaited_once()

        # Query with role filter = 'admin'
        user_service.list.reset_mock()
        params_admin = StaffQueryDTO(role="admin")
        await use_case.execute(params_admin)
        user_service.list.assert_awaited_once()

        # Invalid role
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(StaffQueryDTO(role="invalid_role"))
        assert exc_info.value.status_code == 422

        # Invalid status
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(StaffQueryDTO(status="invalid_status"))
        assert exc_info.value.status_code == 422

    asyncio.run(run_test())


def test_create_staff_use_case():
    async def run_test():
        mock_user = MagicMock(
            id=1,
            public_id=uuid.uuid4(),
            email="newstaff@example.com",
            full_name="New Staff",
            phone="9876543210",
            status=UserStatus.ACTIVE,
            role=UserRole.STAFF,
            is_profile_image_url=None,
            is_subscribed=True,
            created_at=None,
            updated_at=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_email.return_value = None
        user_service.get_user_by_phone.return_value = None
        user_service.create_user.return_value = mock_user

        event_bus = AsyncMock()
        current_user = MagicMock(role=UserRole.ADMIN)

        use_case = CreateStaffUseCase(
            user_service=user_service,
            event_bus=event_bus,
            verify_csrf=False,
            current_user=current_user,
        )

        dto = StaffDTO(
            full_name="New Staff",
            email="newstaff@example.com",
            phone="9876543210",
            role=UserRole.STAFF,
            password="securePassword123!",
            is_subscribed=True,
        )

        result = await use_case.execute(dto)
        assert result.email == "newstaff@example.com"
        assert result.role == UserRole.STAFF
        user_service.create_user.assert_awaited_once()
        event_bus.publish.assert_awaited_once()

        # Test duplicate email
        user_service.get_user_by_email.return_value = mock_user
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto)
        assert exc_info.value.status_code == 409

        # Test duplicate phone
        user_service.get_user_by_email.return_value = None
        user_service.get_user_by_phone.return_value = mock_user
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto)
        assert exc_info.value.status_code == 409

        # Test invalid role
        user_service.get_user_by_phone.return_value = None
        dto_invalid_role = StaffDTO(
            full_name="Invalid Role",
            email="invalid@example.com",
            role="unauthorized_role",
        )
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto_invalid_role)
        assert exc_info.value.status_code == 422

    asyncio.run(run_test())


def test_get_staff_use_case():
    async def run_test():
        staff_id = str(uuid.uuid4())
        mock_staff = MagicMock(
            public_id=staff_id,
            email="staff@example.com",
            full_name="Staff User",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.STAFF,
            is_profile_image_url=None,
            is_subscribed=False,
            created_at=None,
            updated_at=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = mock_staff

        storage_service = MagicMock()
        current_user = MagicMock(role=UserRole.ADMIN)

        use_case = GetStaffUseCase(
            user_service=user_service,
            storage_service=storage_service,
            current_user=current_user,
        )

        result = await use_case.execute(staff_id)
        assert result.id == staff_id
        assert result.email == "staff@example.com"

        # Test not found
        user_service.get_user_by_public_id.return_value = None
        with pytest.raises(AppException) as exc_info:
            await use_case.execute("nonexistent-id")
        assert exc_info.value.status_code == 404

        # Test regular user (not admin/staff)
        mock_user = MagicMock(
            public_id="other-id",
            role=UserRole.USER,
        )
        user_service.get_user_by_public_id.return_value = mock_user
        with pytest.raises(AppException) as exc_info:
            await use_case.execute("other-id")
        assert exc_info.value.status_code == 404

    asyncio.run(run_test())


def test_update_staff_use_case():
    async def run_test():
        mock_user = MagicMock(
            id=1,
            public_id=uuid.uuid4(),
            email="staff@example.com",
            full_name="Old Staff Name",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.STAFF,
            is_profile_image_url=None,
            is_subscribed=False,
            created_at=None,
            updated_at=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = mock_user
        user_service.get_user_by_email.return_value = None
        user_service.get_user_by_phone.return_value = None
        user_service.update.return_value = mock_user

        storage_service = MagicMock()
        current_user = MagicMock(role=UserRole.ADMIN)

        use_case = UpdateStaffUseCase(
            user_service=user_service,
            storage_service=storage_service,
            verify_csrf=False,
            current_user=current_user,
        )

        dto = StaffUpdateDTO(
            full_name="Updated Staff Name",
            email="updatedstaff@example.com",
            role=UserRole.ADMIN,
        )

        result = await use_case.execute(str(mock_user.public_id), dto)
        assert mock_user.full_name == "Updated Staff Name"
        assert mock_user.email == "updatedstaff@example.com"
        assert mock_user.role == UserRole.ADMIN
        user_service.update.assert_awaited_once()

        # Invalid role
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(str(mock_user.public_id), StaffUpdateDTO(role="invalid"))
        assert exc_info.value.status_code == 422

    asyncio.run(run_test())


def test_update_status_staff_use_case():
    async def run_test():
        mock_user = MagicMock(
            id=1,
            public_id=uuid.uuid4(),
            email="staff@example.com",
            full_name="Staff",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.STAFF,
            is_profile_image_url=None,
            is_subscribed=False,
            created_at=None,
            updated_at=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = mock_user
        user_service.update.return_value = mock_user

        storage_service = MagicMock()
        current_user = MagicMock(role=UserRole.ADMIN)

        use_case = UpdateStatusStaffUseCase(
            user_service=user_service,
            storage_service=storage_service,
            verify_csrf=False,
            current_user=current_user,
        )

        result = await use_case.execute(str(mock_user.public_id), "suspended")
        assert mock_user.status == UserStatus.SUSPENDED
        user_service.update.assert_awaited_once()

        # Invalid status check
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(str(mock_user.public_id), "invalid_status")
        assert exc_info.value.status_code == 422

    asyncio.run(run_test())


def test_send_password_reset_link_use_case():
    async def run_test():
        mock_user = MagicMock(
            id=1,
            public_id=uuid.uuid4(),
            email="staff@example.com",
            full_name="Staff",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.STAFF,
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = mock_user

        token_service = AsyncMock()
        token_service.get_active_tokens_by_user_id_and_type.return_value = []
        token_service.create.return_value = MagicMock(token="fake-token")

        event_bus = AsyncMock()
        current_user = MagicMock(role=UserRole.ADMIN)

        use_case = SendStaffPasswordResetLinkUseCase(
            user_service=user_service,
            token_service=token_service,
            event_bus=event_bus,
            verify_csrf=False,
            current_user=current_user,
        )

        dto = StaffResetLinkDTO(confirm="CONFIRM")
        result = await use_case.execute(str(mock_user.public_id), dto)
        assert result["message"] == "Password reset link sent successfully."
        token_service.create.assert_awaited_once()
        event_bus.publish.assert_awaited_once()

        # Test mismatch confirmation string
        invalid_dto = StaffResetLinkDTO(confirm="NO")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(str(mock_user.public_id), invalid_dto)
        assert exc_info.value.status_code == 400

    asyncio.run(run_test())

