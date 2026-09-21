from fastapi.params import Depends

from app.application.use_case.admin.attributes.attribute.create_amenity_use_case import CreateAmenityUseCase
from app.application.use_case.admin.attributes.attribute.get_amenity_use_case import ListAmenitiesUseCase
from app.application.use_case.admin.attributes.attribute.update_amenity_use_case import (
    UpdateAmenityUseCase,
    UpdateStatusAmenityUseCase,
)
from app.application.use_case.vendor.attributes.amenity.create_vendor_amenity_use_case import VendorCreateAmenityUseCase
from app.application.use_case.vendor.attributes.amenity.delete_vendor_amenity_use_case import VendorDeleteAmenityUseCase
from app.application.use_case.vendor.attributes.amenity.list_vendor_amenities_use_case import VendorListAmenitiesUseCase
from app.application.use_case.vendor.attributes.amenity.update_vendor_amenity_status_use_case import VendorUpdateAmenityStatusUseCase
from app.application.use_case.vendor.attributes.amenity.update_vendor_amenity_use_case import VendorUpdateAmenityUseCase
from app.core.csrf import verify_csrf
from app.deps.auth import CurrentUser, require_admin, require_admin_or_staff, require_vendor
from app.deps.service import get_amenity_service, get_storage_service, get_user_service
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService
from app.services.user_service import UserService


async def get_create_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
    user_service: UserService = Depends(get_user_service),
):
    return CreateAmenityUseCase(amenity_service, storage_service, verify_csrf, current_user, user_service)


async def get_list_amenities_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
    user_service: UserService = Depends(get_user_service),
):
    return ListAmenitiesUseCase(amenity_service, storage_service, current_user, user_service)


async def get_vendor_list_amenities_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorListAmenitiesUseCase(amenity_service, storage_service, current_user)


async def get_vendor_create_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorCreateAmenityUseCase(amenity_service, storage_service, verify_csrf, current_user)


async def get_vendor_update_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorUpdateAmenityUseCase(amenity_service, storage_service, current_user)


async def get_vendor_delete_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorDeleteAmenityUseCase(amenity_service, storage_service, current_user)


async def get_vendor_update_status_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorUpdateAmenityStatusUseCase(amenity_service, storage_service, current_user)


async def get_update_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
    user_service: UserService = Depends(get_user_service),
):
    return UpdateAmenityUseCase(amenity_service, storage_service, current_user, user_service)


async def get_update_status_amenity_use_case(
    amenity_service: AmenityService = Depends(get_amenity_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
):
    return UpdateStatusAmenityUseCase(amenity_service, storage_service, current_user)
