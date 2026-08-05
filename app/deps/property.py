from fastapi import Depends

from app.application.use_case.admin.properties.property_use_case import (
    
    ListPropertiesUseCase,
    UpdatePropertyUseCase,
    UpdateStatusPropertyUseCase,
)
from app.application.use_case.admin.properties.create_property_use_case import CreatePropertyUseCase
from app.deps.auth import CurrentUser, require_admin
from app.deps.service import get_property_service
from app.services.property_service import PropertyService


async def get_list_properties_use_case(
    property_service: PropertyService = Depends(get_property_service),
    current_user: CurrentUser = Depends(require_admin),
) -> ListPropertiesUseCase:
    return ListPropertiesUseCase(property_service=property_service, current_user=current_user)


async def get_create_property_use_case(
    property_service: PropertyService = Depends(get_property_service),
    current_user: CurrentUser = Depends(require_admin),
) -> CreatePropertyUseCase:
    return CreatePropertyUseCase(property_service=property_service, current_user=current_user)


async def get_update_property_use_case(
    property_service: PropertyService = Depends(get_property_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdatePropertyUseCase:
    return UpdatePropertyUseCase(property_service=property_service, current_user=current_user)


async def get_update_property_status_use_case(
    property_service: PropertyService = Depends(get_property_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateStatusPropertyUseCase:
    return UpdateStatusPropertyUseCase(property_service=property_service, current_user=current_user)
