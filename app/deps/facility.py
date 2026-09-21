from fastapi.params import Depends

from app.application.use_case.admin.attributes.attribute.create_facility_use_case import  CreateFacilityUseCase
from app.application.use_case.admin.attributes.attribute.get_facility_use_case import ListFacilitiesUseCase
from app.application.use_case.admin.attributes.attribute.update_facility_use_case import (
    UpdateFacilityUseCase,
    UpdateStatusFacilityUseCase,
)
from app.application.use_case.vendor.attributes.facility.create_vendor_facility_use_case import VendorCreateFacilityUseCase
from app.application.use_case.vendor.attributes.facility.delete_vendor_facility_use_case import VendorDeleteFacilityUseCase
from app.application.use_case.vendor.attributes.facility.list_vendor_facilities_use_case import VendorListFacilitiesUseCase
from app.application.use_case.vendor.attributes.facility.update_vendor_facility_status_use_case import VendorUpdateFacilityStatusUseCase
from app.application.use_case.vendor.attributes.facility.update_vendor_facility_use_case import VendorUpdateFacilityUseCase
from app.core.csrf import verify_csrf
from app.deps.auth import CurrentUser, require_admin, require_admin_or_staff, require_vendor
from app.deps.service import get_facility_service, get_storage_service, get_user_service
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService
from app.services.user_service import UserService


async def get_create_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
    user_service: UserService = Depends(get_user_service),
):
    return CreateFacilityUseCase(facility_service, storage_service, verify_csrf, current_user, user_service)


async def get_list_facilities_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
    user_service: UserService = Depends(get_user_service),
) -> ListFacilitiesUseCase:
    return ListFacilitiesUseCase(facility_service, storage_service, verify_csrf, current_user, user_service)


async def get_vendor_list_facilities_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorListFacilitiesUseCase:
    return VendorListFacilitiesUseCase(facility_service, storage_service, current_user)


async def get_vendor_create_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorCreateFacilityUseCase(facility_service, storage_service, verify_csrf, current_user)


async def get_vendor_update_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorUpdateFacilityUseCase(facility_service, storage_service, current_user)


async def get_vendor_delete_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorDeleteFacilityUseCase(facility_service, storage_service, current_user)


async def get_vendor_update_status_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorUpdateFacilityStatusUseCase(facility_service, storage_service, current_user)


async def get_update_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
    user_service: UserService = Depends(get_user_service),
):
    return UpdateFacilityUseCase(facility_service, storage_service, current_user, user_service)


async def get_update_status_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
):
    return UpdateStatusFacilityUseCase(facility_service, storage_service, current_user)
