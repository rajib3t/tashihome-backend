from app.application.dto.vendors.vendor import VendorQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import User, UserRole, UserStatus
from app.repositories.base_repository import Page
from app.schemas.user_schema import UserData
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class ListVendorUseCase(BaseUseCase):
    def __init__(
            self, 
            user_service: UserService,
            storage_service: StorageService,
            current_user: CurrentUser 
        ):
        self.user_service = user_service
        self.storage_service = storage_service
        self.current_user = current_user
    async def execute(self, params: VendorQueryDTO) -> Page[UserData]:
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
        items = []
        for vendor in vendors_page.items:
            profile_image_url =  vendor.is_profile_image_url
            items.append(
                UserData(
                    id=vendor.public_id,
                    email=vendor.email,
                    full_name=vendor.full_name or "",
                    phone=vendor.phone,
                    status=vendor.status,
                    role=vendor.role,
                    is_profile_image_url=profile_image_url,
                )
            )

        return Page(
            items=items,
            total=vendors_page.total,
            page=vendors_page.page,
            page_size=vendors_page.page_size,
        )
         
