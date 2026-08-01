from app.application.dto.vendors.vendor import VendorQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import User, UserRole, UserStatus
from app.repositories.base_repository import Page
from app.services.user_service import UserService


class ListVendorUseCase(BaseUseCase):
    def __init__(
            self, 
            user_service: UserService,
            current_user: CurrentUser 
        ):
        self.user_service = user_service
        self.current_user = current_user
    async def execute(self, params: VendorQueryDTO) -> Page[User]:
        filters = list(params.filters or [])

        if params.full_name:
            filters.append({"name": "full_name", "value": params.full_name})
        if params.email:
            filters.append({"name": "email", "value": params.email})
        if params.phone:
            filters.append({"name": "phone", "value": params.phone})
        if params.status:
                    if params.status not in ["active", "inactive"]:
                        raise AppException(
                            status_code=422,
                            message="Invalid status filter. Must be 'active' or 'inactive'.",
                            field="status",
                            error_code="STATUS_INVALID",
                        )
                    if params.status == "active":
                        filters.append({"name": "status", "value": UserStatus.ACTIVE})
                    elif params.status == "inactive":
                        filters.append({"name": "status", "value": UserStatus.INACTIVE})
        
        filters.append({"name": "role", "value": UserRole.VENDOR})


        vendors_page = await self.user_service.list(
            page=params.page,
            page_size=params.size,
            filters=filters,
            flush=True,
        )

        return vendors_page
         