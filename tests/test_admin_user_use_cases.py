import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.users.user import (
    UserDTO,
    UserQueryDTO,
    UserResetLinkDTO,
    UserUpdateDTO,
)
from app.application.use_case.admin.users.create_user_use_case import CreateUserUseCase
from app.application.use_case.admin.users.get_user_use_case import GetUserUseCase
from app.application.use_case.admin.users.list_user_use_case import ListUserUseCase
from app.application.use_case.admin.users.send_password_reset_link_use_case import (
    SendUserPasswordResetLinkUseCase,
)
from app.application.use_case.admin.users.update_user_use_case import (
    UpdateStatusUserUseCase,
    UpdateUserUseCase,
)
from app.core.exceptions import AppException
from app.models.user_model import UserRole, UserStatus
from app.repositories.base_repository import Page


def test_list_user_use_case():
    async def run_test():
        mock_user = MagicMock(
            public_id=uuid.uuid4(),
            email="test@example.com",
            full_name="Test User",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
            is_profile_image_url=None,
            is_subscribed=True,
            created_at=None,
            updated_at=None,
        )

        user_service = AsyncMock()
        user_service.list.return_value = Page(
            items=[mock_user],
            total=1,
            page=1,
            page_size=10,
        )

        storage_service = MagicMock()
        current_user = MagicMock(role=UserRole.ADMIN)

        use_case = ListUserUseCase(
            user_service=user_service,
            storage_service=storage_service,
            current_user=current_user,
        )

        params = UserQueryDTO(page=1, size=10, email="test@example.com", status="active")
        result = await use_case.execute(params)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].email == "test@example.com"
        assert result.items[0].full_name == "Test User"
        user_service.list.assert_awaited_once()

    asyncio.run(run_test())


def test_get_user_use_case():
    async def run_test():
        user_id = str(uuid.uuid4())
        mock_user = MagicMock(
            public_id=user_id,
            email="test@example.com",
            full_name="Test User",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
            is_profile_image_url=None,
            is_subscribed=False,
            created_at=None,
            updated_at=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = mock_user

        storage_service = MagicMock()
        current_user = MagicMock(role=UserRole.ADMIN)

        use_case = GetUserUseCase(
            user_service=user_service,
            storage_service=storage_service,
            current_user=current_user,
        )

        result = await use_case.execute(user_id)
        assert result.id == user_id
        assert result.email == "test@example.com"

        # Test not found
        user_service.get_user_by_public_id.return_value = None
        with pytest.raises(AppException) as exc_info:
            await use_case.execute("nonexistent-id")
        assert exc_info.value.status_code == 404

    asyncio.run(run_test())


def test_create_user_use_case():
    async def run_test():
        mock_user = MagicMock(
            id=1,
            public_id=uuid.uuid4(),
            email="newuser@example.com",
            full_name="New User",
            phone="9876543210",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
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

        use_case = CreateUserUseCase(
            user_service=user_service,
            event_bus=event_bus,
            verify_csrf=False,
            current_user=current_user,
        )

        dto = UserDTO(
            full_name="New User",
            email="newuser@example.com",
            phone="9876543210",
            password="securePassword123!",
            is_subscribed=True,
        )

        result = await use_case.execute(dto)
        assert result.email == "newuser@example.com"
        assert result.full_name == "New User"
        user_service.create_user.assert_awaited_once()
        event_bus.publish.assert_awaited_once()

    asyncio.run(run_test())


def test_update_user_use_case():
    async def run_test():
        mock_user = MagicMock(
            id=1,
            public_id=uuid.uuid4(),
            email="user@example.com",
            full_name="Old Name",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
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

        use_case = UpdateUserUseCase(
            user_service=user_service,
            storage_service=storage_service,
            verify_csrf=False,
            current_user=current_user,
        )

        dto = UserUpdateDTO(
            full_name="Updated Name",
            email="updated@example.com",
            status="inactive",
        )

        result = await use_case.execute(str(mock_user.public_id), dto)
        assert mock_user.full_name == "Updated Name"
        assert mock_user.email == "updated@example.com"
        assert mock_user.status == UserStatus.INACTIVE
        user_service.update.assert_awaited_once()

    asyncio.run(run_test())


def test_update_status_user_use_case():
    async def run_test():
        mock_user = MagicMock(
            id=1,
            public_id=uuid.uuid4(),
            email="user@example.com",
            full_name="User",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
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

        use_case = UpdateStatusUserUseCase(
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
            email="user@example.com",
            full_name="User",
            phone="1234567890",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = mock_user

        token_service = AsyncMock()
        token_service.get_active_tokens_by_user_id_and_type.return_value = []
        token_service.create.return_value = MagicMock(token="fake-token")

        event_bus = AsyncMock()
        current_user = MagicMock(role=UserRole.ADMIN)

        use_case = SendUserPasswordResetLinkUseCase(
            user_service=user_service,
            token_service=token_service,
            event_bus=event_bus,
            verify_csrf=False,
            current_user=current_user,
        )

        dto = UserResetLinkDTO(confirm="CONFIRM")
        result = await use_case.execute(str(mock_user.public_id), dto)
        assert result["message"] == "Password reset link sent successfully."
        token_service.create.assert_awaited_once()
        event_bus.publish.assert_awaited_once()

        # Test mismatch confirmation string
        invalid_dto = UserResetLinkDTO(confirm="NO")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(str(mock_user.public_id), invalid_dto)
        assert exc_info.value.status_code == 400

    asyncio.run(run_test())

