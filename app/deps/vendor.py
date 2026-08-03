
from app.application.use_case.admin.vendors.get_vendor_use_case import GetVendorUseCase
from app.application.use_case.admin.vendors.update_vendor_use_case import UpdateVendorUseCase, UploadVendorProfileImageUseCase
from app.application.use_case.admin.vendors.list_vendor_use_case import ListVendorUseCase
from app.deps.event_bus import get_event_bus
from app.core.events import EventBus
from fastapi.params import Depends

from app.application.use_case.admin.vendors.create_vendor_use_case import CreateVendorUseCase
from app.core.csrf import verify_csrf
from app.deps.auth import CurrentUser, require_admin
from app.deps.database import get_db
from app.deps.service import get_storage_service, get_user_service
from app.services.address_service import AddressService
from app.services.company_service import CompanyService
from app.services.storage_service import StorageService
from app.services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession


async def get_create_vendor_use_case(
    user_service: UserService = Depends(get_user_service),
    event_bus: EventBus = Depends(get_event_bus),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin),
) -> CreateVendorUseCase:
    return CreateVendorUseCase(
        user_service=user_service,
        event_bus=event_bus,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )

async def get_list_vendor_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> ListVendorUseCase:
    return ListVendorUseCase(
        user_service=user_service,
        storage_service=storage_service,
        current_user=current_user,
    )


async def get_vendor_use_case(
        user_service: UserService = Depends(get_user_service),
        storage_service : StorageService = Depends(get_storage_service),
        current_user: CurrentUser = Depends(require_admin),
) -> GetVendorUseCase:
    return GetVendorUseCase(
        user_service=user_service,
        storage_service=storage_service,

        current_user=current_user
    )


async def get_update_vendor_use_case(
        user_service: UserService = Depends(get_user_service),
        storage_service: StorageService = Depends(get_storage_service),
        verify_csrf=Depends(verify_csrf),
        current_user: CurrentUser = Depends(require_admin),
) -> UpdateVendorUseCase:
    return UpdateVendorUseCase(
        user_service=user_service,
        storage_service=storage_service,
        company_service=user_service.company_service,
        address_service=user_service.address_service,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )


async def get_upload_vendor_profile_image_use_case(
        user_service: UserService = Depends(get_user_service),
        storage_service: StorageService = Depends(get_storage_service),
        verify_csrf=Depends(verify_csrf),
        current_user: CurrentUser = Depends(require_admin),
) -> UploadVendorProfileImageUseCase:
    return UploadVendorProfileImageUseCase(
        user_service=user_service,
        storage_service=storage_service,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )
