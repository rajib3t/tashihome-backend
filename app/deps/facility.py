from fastapi.params import Depends

from app.application.use_case.admin.attributes.attribute.create_facility_use_case import  CreateFacilityUseCase
from app.application.use_case.admin.attributes.attribute.get_facility_use_case import ListFacilitiesUseCase
from app.application.use_case.admin.attributes.attribute.update_facility_use_case import (
    UpdateFacilityUseCase,
    UpdateStatusFacilityUseCase,
)
from app.core.csrf import verify_csrf
from app.deps.auth import CurrentUser, require_admin, require_admin_or_staff, require_vendor
from app.deps.service import  get_facility_service, get_storage_service
from app.services.facility_service import  FacilityService
from app.services.storage_service import StorageService


async def get_create_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service : StorageService = Depends(get_storage_service),
    verify_csrf = Depends(verify_csrf),
    current_user : CurrentUser = Depends(require_admin_or_staff),
):
    return CreateFacilityUseCase(facility_service, storage_service, verify_csrf, current_user)


async def get_list_facilities_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service : StorageService = Depends(get_storage_service),
    verify_csrf = Depends(verify_csrf),
    current_user : CurrentUser = Depends(require_admin_or_staff),
) -> ListFacilitiesUseCase:
    return ListFacilitiesUseCase(facility_service, storage_service,verify_csrf, current_user)


async def get_vendor_list_facilities_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service : StorageService = Depends(get_storage_service),
    verify_csrf = Depends(verify_csrf),
    current_user : CurrentUser = Depends(require_admin_or_staff),
) ->ListFacilitiesUseCase:
    return ListFacilitiesUseCase(facility_service, storage_service, verify_csrf, current_user)


async def get_update_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
):
    return UpdateFacilityUseCase(facility_service, storage_service, current_user)


async def get_update_status_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
):
    return UpdateStatusFacilityUseCase(facility_service, storage_service, current_user)
