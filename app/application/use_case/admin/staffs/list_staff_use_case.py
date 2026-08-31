from app.application.dto.staffs.staff import StaffQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import UserRole, UserStatus
from app.repositories.base_repository import Page
from app.schemas.user_schema import UserData
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class ListStaffUseCase(BaseUseCase):
    def __init__(
        self,
        user_service: UserService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, params: StaffQueryDTO) -> Page[UserData]:
        filters = list(params.filters or [])

        if params.full_name:
            filters.append({"name": "full_name", "value": params.full_name})
        if params.email:
            filters.append({"name": "email", "value": params.email})
        if params.phone:
            filters.append({"name": "phone", "value": params.phone})

        if params.status:
            normalized_status = params.status.strip().lower()
            valid_statuses = {
                "active": UserStatus.ACTIVE,
                "inactive": UserStatus.INACTIVE,
                "suspended": UserStatus.SUSPENDED,
            }
            if normalized_status not in valid_statuses:
                raise AppException(
                    status_code=422,
                    message="Invalid status filter. Must be 'active', 'inactive', or 'suspended'.",
                    field="status",
                    error_code="STATUS_INVALID",
                )
            filters.append({"name": "status", "value": valid_statuses[normalized_status]})

        if params.role:
            role_val = params.role.value if hasattr(params.role, "value") else str(params.role)
            normalized_role = role_val.strip().lower()
            valid_roles = {
                "admin": UserRole.ADMIN,
                "staff": UserRole.STAFF,
            }
            if normalized_role not in valid_roles:
                raise AppException(
                    status_code=422,
                    message="Invalid role filter. Must be 'admin' or 'staff'.",
                    field="role",
                    error_code="ROLE_INVALID",
                )
            filters.append({"name": "role", "value": valid_roles[normalized_role]})
        else:
            filters.append({"name": "role", "value": [UserRole.ADMIN, UserRole.STAFF]})

        users_page = await self.user_service.list(
            page=params.page,
            page_size=params.size,
            filters=filters,
            flush=True,
        )

        items = []
        for user in users_page.items:
            items.append(
                UserData(
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
            )

        return Page(
            items=items,
            total=users_page.total,
            page=users_page.page,
            page_size=users_page.page_size,
        )

