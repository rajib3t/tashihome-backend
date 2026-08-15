from app.application.use_case.admin.properties.upload_property_assets_use_case import DeletePropertyAssetUseCase
from fastapi import Depends

from app.application.use_case.admin.properties.get_properties_use_case import GetPropertiesUseCase
from app.application.use_case.admin.properties.get_property_use_case import GetPropertyUseCase
from app.application.use_case.admin.properties.property_use_case import (
    
    ListPropertiesUseCase,
    UpdateStatusPropertyUseCase,
)
from app.application.use_case.admin.properties.update_property_use_case import UpdatePropertyUseCase
from app.application.use_case.admin.properties.upload_property_assets_use_case import UploadPropertyAssetsUseCase
from app.application.use_case.admin.properties.create_property_use_case import CreatePropertyUseCase
from app.deps.auth import CurrentUser, require_admin
from app.deps.service import (
    get_amenity_service,
    get_city_service,
    get_facility_service,
    get_location_service,
    get_property_amenity_service,
    get_property_facility_service,
    get_property_food_option_service,
    get_property_asset_service,
    get_property_service,
    get_storage_service,
    get_property_room_type_service,
    get_room_type_service,
    get_user_service,
)
from app.services.amenity_service import AmenityService
from app.services.facility_service import FacilityService
from app.services.city_service import CityService
from app.services.room_type_service import RoomTypeService
from app.services.location_service import LocationService
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService
from app.services.property_amenity_service import PropertyAmenityService
from app.services.property_facility_service import PropertyFacilityService
from app.services.property_food_option_service import PropertyFoodOptionService
from app.services.property_asset_service import PropertyAssetService
from app.services.property_room_type_service import PropertyRoomTypeService
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
    amenity_service: AmenityService = Depends(get_amenity_service),
    facility_service: FacilityService = Depends(get_facility_service),
    property_amenity_service: PropertyAmenityService = Depends(get_property_amenity_service),
    property_facility_service: PropertyFacilityService = Depends(get_property_facility_service),
    property_food_option_service: PropertyFoodOptionService = Depends(get_property_food_option_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> CreatePropertyUseCase:
    return CreatePropertyUseCase(
        property_service=property_service,
        user_service=user_service,
        city_service=city_service,
        location_service=location_service,
        amenity_service=amenity_service,
        facility_service=facility_service,
        property_amenity_service=property_amenity_service,
        property_facility_service=property_facility_service,
        property_food_option_service=property_food_option_service,
        storage_service=storage_service,
        current_user=current_user,
    )


async def get_update_property_use_case(
    property_service: PropertyService = Depends(get_property_service),
    city_service: CityService = Depends(get_city_service),
    location_service: LocationService = Depends(get_location_service),
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    amenity_service: AmenityService = Depends(get_amenity_service),
    facility_service: FacilityService = Depends(get_facility_service),
    property_amenity_service: PropertyAmenityService = Depends(get_property_amenity_service),
    property_facility_service: PropertyFacilityService = Depends(get_property_facility_service),
    property_food_option_service: PropertyFoodOptionService = Depends(get_property_food_option_service),
    property_room_type_service: PropertyRoomTypeService = Depends(get_property_room_type_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdatePropertyUseCase:
    return UpdatePropertyUseCase(
        property_service=property_service,
        city_service=city_service,
        location_service=location_service,
        room_type_service=room_type_service,
        amenity_service=amenity_service,
        facility_service=facility_service,
        property_amenity_service=property_amenity_service,
        property_facility_service=property_facility_service,
        property_food_option_service=property_food_option_service,
        property_room_type_service=property_room_type_service,
        storage_service=storage_service,
        current_user=current_user,
    )


async def get_update_property_status_use_case(
    property_service: PropertyService = Depends(get_property_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateStatusPropertyUseCase:
    return UpdateStatusPropertyUseCase(
        property_service=property_service,
        storage_service=storage_service,
        current_user=current_user,
    )



async def get_property_use_case(
    property_service: PropertyService = Depends(get_property_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> GetPropertyUseCase:
    return GetPropertyUseCase(property_service=property_service, storage_service=storage_service, current_user=current_user)


async def get_upload_property_assets_use_case(
    property_service: PropertyService = Depends(get_property_service),
    property_asset_service: PropertyAssetService = Depends(get_property_asset_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UploadPropertyAssetsUseCase:
    return UploadPropertyAssetsUseCase(
        property_service=property_service,
        property_asset_service=property_asset_service,
        storage_service=storage_service,
        current_user=current_user,
    )


async def get_delete_property_asset_use_case(
    property_service: PropertyService = Depends(get_property_service),
    property_asset_service: PropertyAssetService = Depends(get_property_asset_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> DeletePropertyAssetUseCase:
    return DeletePropertyAssetUseCase(
        property_service=property_service,
        property_asset_service=property_asset_service,
        storage_service=storage_service,
        current_user=current_user,
    )