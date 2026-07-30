from fastapi.params import Depends

from app.application.use_case.attributes.attribute.create_facility_use_base import  CreateFacilityUseCase
from app.deps.auth import CurrentUser, require_admin
from app.deps.service import  get_facility_service, get_storage_service
from app.services.facility_service import  FacilityService
from app.services.storage_service import StorageService


async def get_create_facility_use_case(
    facility_service: FacilityService = Depends(get_facility_service),
    storage_service : StorageService = Depends(get_storage_service),
    current_user : CurrentUser = Depends(require_admin),
):
    return CreateFacilityUseCase(facility_service, storage_service, current_user)