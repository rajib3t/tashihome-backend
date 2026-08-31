from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import UserRole
from app.schemas.user_schema import UserData
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class GetStaffUseCase(BaseUseCase):
    def __init__(
        self,
        user_service: UserService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, staff_id: str) -> UserData:
        user = await self.user_service.get_user_by_public_id(public_id=staff_id)

        if not user or user.role not in (UserRole.ADMIN, UserRole.STAFF):
            raise AppException(
                status_code=404,
                message="Staff not found",
                error_code="USER_NOT_FOUND",
                field="staff_id",
            )

        return UserData(
            id=str(user.public_id),
            email=user.email,
            full_name=user.full_name or "",
            phone=user.phone,
            status=user.status.value if hasattr(user.status, "value") else str(user.status),
            role=user.role,
            is_profile_image_url=user.is_profile_image_url,
            is_subscribed=user.is_subscribed,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

