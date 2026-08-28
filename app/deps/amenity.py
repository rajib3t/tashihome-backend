from fastapi.params import Depends

from app.application.use_case.admin.attributes.attribute.create_amenity_use_case import CreateAmenityUseCase
from app.application.use_case.admin.attributes.attribute.get_amenity_use_case import ListAmenitiesUseCase
from app.application.use_case.admin.attributes.attribute.update_amenity_use_case import (
    UpdateAmenityUseCase,
    UpdateStatusAmenityUseCase,
)
from app.core.csrf import verify_csrf
from app.deps.auth import CurrentUser, require_admin, require_vendor
from app.deps.service import get_amenity_service, get_storage_service
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService


async def get_create_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin),
):
    return CreateAmenityUseCase(amenity_service, storage_service, verify_csrf, current_user)


async def get_list_amenities_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
):
    return ListAmenitiesUseCase(amenity_service, storage_service, current_user)

async def get_vendor_list_amenities_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return ListAmenitiesUseCase(amenity_service, storage_service, current_user)

async def get_update_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
):
    return UpdateAmenityUseCase(amenity_service, storage_service, current_user)


async def get_update_status_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
):
    return UpdateStatusAmenityUseCase(amenity_service, storage_service, current_user)
