from typing import Optional

from app.application.dto.properties.property import PropertyUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.property_amenity_model import PropertyAmenity
from app.models.property_facility_model import PropertyFacility
from app.models.property_food_option_model import PropertyFoodOption, PropertyFoodOptionStatus
from app.models.property_room_type_model import PropertyRoomType
from app.models.property_model import Property, PropertyStatus
from app.services.amenity_service import AmenityService
from app.services.city_service import CityService
from app.services.facility_service import FacilityService
from app.services.location_service import LocationService
from app.services.property_amenity_service import PropertyAmenityService
from app.services.property_facility_service import PropertyFacilityService
from app.services.property_food_option_service import PropertyFoodOptionService
from app.services.property_room_type_service import PropertyRoomTypeService
from app.services.property_service import PropertyService
from app.services.room_type_service import RoomTypeService
from app.services.storage_service import StorageService
from app.utils.slug import generate_slug


class UpdatePropertyUseCase(PropertySerializerMixin, BaseUseCase):
    def __init__(
        self,
        property_service: PropertyService,
        city_service: CityService,
        location_service: LocationService,
        room_type_service: RoomTypeService,
        amenity_service: AmenityService,
        facility_service: FacilityService,
        property_amenity_service: PropertyAmenityService,
        property_facility_service: PropertyFacilityService,
        property_food_option_service: PropertyFoodOptionService,
        property_room_type_service: PropertyRoomTypeService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.property_service = property_service
        self.city_service = city_service
        self.location_service = location_service
        self.room_type_service = room_type_service
        self.amenity_service = amenity_service
        self.facility_service = facility_service
        self.property_amenity_service = property_amenity_service
        self.property_facility_service = property_facility_service
        self.property_food_option_service = property_food_option_service
        self.property_room_type_service = property_room_type_service
        self.storage_service = storage_service
        self.current_user = current_user

    @staticmethod
    def _normalize_status(status_value: Optional[str]) -> PropertyStatus:
        status_text = (status_value or "draft").strip().lower()
        valid_statuses = {item.value for item in PropertyStatus}
        if status_text not in valid_statuses:
            raise AppException(
                status_code=422,
                message="Status must be one of: draft, active, inactive, archived.",
                field="status",
                error_code="STATUS_INVALID",
            )
        return PropertyStatus(status_text)

    async def execute(self, property_id: str, data: PropertyUpdateDTO) -> dict:
        existing_property = await self.property_service.get_by_public_id(property_id, flush=False)
        if not existing_property:
            raise AppException(
                status_code=404,
                message="Property not found.",
                field="property_id",
                error_code="PROPERTY_NOT_FOUND",
            )

        if data.name is not None:
            normalized_name = data.name.strip()
            duplicate_name = await self.property_service.get_by_vendor_and_name(existing_property.vendor_id, normalized_name, flush=True)
            if duplicate_name and duplicate_name.id != existing_property.id:
                raise AppException(
                    status_code=409,
                    message="A property with this name already exists for this vendor.",
                    field="name",
                    error_code="PROPERTY_NAME_EXIST",
                )
            existing_property.name = normalized_name

        if data.slug is not None:
            normalized_slug = await generate_slug(data.slug)
            duplicate_slug = await self.property_service.get_by_vendor_and_slug(existing_property.vendor_id, normalized_slug, flush=True)
            if duplicate_slug and duplicate_slug.id != existing_property.id:
                raise AppException(
                    status_code=409,
                    message="A property with this slug already exists for this vendor.",
                    field="slug",
                    error_code="PROPERTY_SLUG_EXIST",
                )
            existing_property.slug = normalized_slug

        if data.description is not None:
            existing_property.description = data.description.strip()

        if data.location_id is not None:
            location = await self.location_service.get_by_public_id(data.location_id, flush=True)
            if not location:
                raise AppException(
                    status_code=404,
                    message="Location not found.",
                    field="location_id",
                    error_code="LOCATION_NOT_FOUND",
                )
            existing_property.location_id = location.id

        if data.city_id is not None:
            city = await self.city_service.get_by_public_id(data.city_id, flush=True)
            if not city:
                raise AppException(
                    status_code=404,
                    message="City not found.",
                    field="city_id",
                    error_code="CITY_NOT_FOUND",
                )
            existing_property.city_id = city.id
        if data.address is not None:
            existing_property.address = data.address.strip()
        if data.price_per_night is not None:
            existing_property.price_per_night = data.price_per_night
        if data.price is not None:
            existing_property.price_per_night = data.price
        if data.sale_per_night is not None:
            existing_property.sale_per_night = data.sale_per_night
        if data.sale_price is not None:
            existing_property.sale_per_night = data.sale_price

        if data.price_per_night > 0 and data.sale_per_night is not None and data.sale_per_night > data.price_per_night:
            raise AppException(
                status_code=422,
                message="Sale price per night cannot be greater than the regular price per night.",
                field="sale_per_night",
                error_code="SALE_PRICE_INVALID",
            )
        if data.currency is not None:
            existing_property.currency = data.currency.upper()
        if data.latitude is not None:
            existing_property.latitude = data.latitude
        if data.longitude is not None:
            existing_property.longitude = data.longitude
        if data.is_featured is not None:
            existing_property.is_featured = data.is_featured
        if data.type is not None:
            existing_property.type = data.type
        if data.status is not None:
            existing_property.status = self._normalize_status(data.status)

        existing_property.updated_by = self.current_user.id
        updated_property = await self.property_service.update(existing_property)
        await self._sync_child_records(updated_property.id, data)

        full_property = await self.property_service.get_by_public_id(
            updated_property.public_id,
            with_relations={
                "vendor": True,
                "city": True,
                "location": True,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
                "property_food_options": True,
                "property_assets": True,
            },
            flush=True,
        ) or updated_property
        return await self.serialize_property(full_property)

    async def _sync_child_records(self, property_id: int, data: PropertyUpdateDTO) -> None:
        # The update DTO has `amenities: List[PropertyAmenitiesDTO]` (objects with .id)
        # and `amenity_ids: List[str]` (flat strings). Support both.
        amenity_ids = data.amenity_ids
        if amenity_ids is None and data.amenities is not None:
            amenity_ids = [a.id for a in data.amenities if getattr(a, "id", None)]

        if amenity_ids is not None:
            existing_amenities = await self.property_amenity_service.get_by_property_id(property_id, flush=True)
            for item in existing_amenities:
                await self.property_amenity_service.delete(item, commit=True)

            for amenity_id in amenity_ids:
                amenity = await self.amenity_service.get_by_public_id(amenity_id, flush=True)
                if not amenity:
                    raise AppException(
                        status_code=404,
                        message="Amenity not found.",
                        field="amenities",
                        error_code="AMENITY_NOT_FOUND",
                    )
                await self.property_amenity_service.create(
                    PropertyAmenity(property_id=property_id, amenity_id=amenity.id),
                    commit=True,
                )

        # The update DTO has `facility: List[PropertyFacilityDTO]`, `facilities: List[PropertyFacilityDTO]`, and `facility_ids: List[str]`
        facility_ids = data.facility_ids
        if facility_ids is None:
            if data.facility is not None:
                facility_ids = [f.id for f in data.facility if getattr(f, "id", None)]
            elif data.facilities is not None:
                facility_ids = [f.id for f in data.facilities if getattr(f, "id", None)]

        if facility_ids is not None:
            existing_facilities = await self.property_facility_service.get_by_property_id(property_id, flush=True)
            for item in existing_facilities:
                await self.property_facility_service.delete(item, commit=True)

            for facility_id in facility_ids:
                facility = await self.facility_service.get_by_public_id(facility_id, flush=True)
                if not facility:
                    raise AppException(
                        status_code=404,
                        message="Facility not found.",
                        field="facility",
                        error_code="FACILITY_NOT_FOUND",
                    )
                await self.property_facility_service.create(
                    PropertyFacility(property_id=property_id, facility_id=facility.id),
                    commit=True,
                )

        food_option_names = data.food_option_ids
        if food_option_names is None and data.food_options is not None:
            food_option_names = [fo.name for fo in data.food_options if getattr(fo, "name", None)]

        if food_option_names is not None:
            existing_food_options = await self.property_food_option_service.get_by_property_id(property_id, flush=True)
            for item in existing_food_options:
                await self.property_food_option_service.delete(item, commit=True)

            for food_name in food_option_names:
                await self.property_food_option_service.create(
                    PropertyFoodOption(
                        property_id=property_id,
                        name=food_name,
                        is_included=True,
                        status=PropertyFoodOptionStatus.ACTIVE,
                    ),
                    commit=True,
                )

        room_types_data = None
        if data.room_types is not None:
            room_types_data = []
            for rt in data.room_types:
                rt_id = getattr(rt, "room_type_id", None) or getattr(rt, "id", None)
                if rt_id:
                    units = getattr(rt, "total_units", None)
                    units = units if units is not None else 1
                    room_types_data.append((rt_id, units))
        elif data.room_type_ids is not None:
            room_types_data = [(rt_id, 1) for rt_id in data.room_type_ids if rt_id]
        elif data.room_type_id is not None:
            room_types_data = [(data.room_type_id, 1)]

        if room_types_data is not None:
            existing_room_types = await self.property_room_type_service.get_by_property_id(property_id, flush=True)
            for item in existing_room_types:
                await self.property_room_type_service.delete(item, commit=True)

            for rt_id, units in room_types_data:
                if units < 1:
                    raise AppException(
                        status_code=422,
                        message="Total units must be greater than 0.",
                        field="total_units",
                        error_code="TOTAL_UNITS_INVALID",
                    )
                room_type = await self.room_type_service.get_by_public_id(rt_id, flush=True)
                if not room_type:
                    raise AppException(
                        status_code=404,
                        message="Room type not found.",
                        field="room_type_ids",
                        error_code="ROOM_TYPE_NOT_FOUND",
                    )
                await self.property_room_type_service.create(
                    PropertyRoomType(
                        property_id=property_id,
                        room_type_id=room_type.id,
                        total_units=units,
                    ),
                    commit=True,
                )
