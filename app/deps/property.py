from fastapi import Depends

from app.application.use_case.admin.properties.get_properties_use_case import GetPropertiesUseCase
from app.application.use_case.admin.properties.get_property_use_case import GetPropertyUseCase
from app.application.use_case.admin.properties.property_use_case import (
    
    ListPropertiesUseCase,
    UpdatePropertyUseCase,
    UpdateStatusPropertyUseCase,
)
from app.application.use_case.admin.properties.create_property_use_case import CreatePropertyUseCase
from app.deps.auth import CurrentUser, require_admin
from app.deps.service import get_city_service, get_location_service, get_property_service, get_storage_service, get_user_service
from app.services.city_service import CityService
from app.services.location_service import LocationService
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService
from app.services.user_service import UserService


async def get_list_properties_use_case(
    property_service: PropertyService = Depends(get_property_service),
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> GetPropertiesUseCase:
    return GetPropertiesUseCase(property_service=property_service, user_service=user_service, storage_service=storage_service, current_user=current_user)


async def get_create_property_use_case(
    property_service: PropertyService = Depends(get_property_service),
    user_service: UserService = Depends(get_user_service),
    city_service: CityService = Depends(get_city_service),
    location_service: LocationService = Depends(get_location_service),
    current_user: CurrentUser = Depends(require_admin),
) -> CreatePropertyUseCase:
    return CreatePropertyUseCase(
        property_service=property_service, 
        user_service=user_service, 
        city_service=city_service, 
        location_service=location_service, 
        current_user=current_user
    )


async def get_update_property_use_case(
    property_service: PropertyService = Depends(get_property_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdatePropertyUseCase:
    return UpdatePropertyUseCase(property_service=property_service, storage_service=storage_service, current_user=current_user)


async def get_update_property_status_use_case(
    property_service: PropertyService = Depends(get_property_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateStatusPropertyUseCase:
    return UpdateStatusPropertyUseCase(property_service=property_service, storage_service=storage_service, current_user=current_user)



async def get_property_use_case(
    property_service: PropertyService = Depends(get_property_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> GetPropertyUseCase:
    return GetPropertyUseCase(property_service=property_service, storage_service=storage_service)