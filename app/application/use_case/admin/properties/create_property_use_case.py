from app.application.use_case.base_use_case import BaseUseCase
from app.models.property_model import Property
from app.models.property_amenity_model import PropertyAmenity
from app.models.property_facility_model import PropertyFacility
from app.models.property_food_option_model import PropertyFoodOption, PropertyFoodOptionStatus
from app.services.city_service import CityService
from app.services.amenity_service import AmenityService
from app.services.facility_service import FacilityService
from app.services.property_amenity_service import PropertyAmenityService
from app.services.property_facility_service import PropertyFacilityService
from app.services.property_food_option_service import PropertyFoodOptionService
from app.services.location_service import LocationService
from app.services.property_service import PropertyService
from app.deps.auth import CurrentUser
from app.application.dto.properties.property import PropertyDTO
from typing import Optional
from app.core.exceptions import AppException
from app.services.user_service import UserService
from app.utils.slug import generate_slug


class CreatePropertyUseCase(BaseUseCase):
    def __init__(
        self,
        property_service: PropertyService,
        user_service: UserService,
        city_service: CityService,
        location_service: LocationService,
        amenity_service: AmenityService,
        facility_service: FacilityService,
        property_amenity_service: PropertyAmenityService,
        property_facility_service: PropertyFacilityService,
        property_food_option_service: PropertyFoodOptionService,
        current_user: CurrentUser
    ):
        self.property_service = property_service
        self.user_service = user_service
        self.city_service = city_service
        self.location_service = location_service
        self.amenity_service = amenity_service
        self.facility_service = facility_service
        self.property_amenity_service = property_amenity_service
        self.property_facility_service = property_facility_service
        self.property_food_option_service = property_food_option_service
        self.current_user = current_user

    async def execute(self, property_dto: PropertyDTO) -> Optional[Property]:
        # Validate and resolve IDs

        if property_dto.vendor_id is None:
            raise AppException(
                status_code=422,
                message="vendor is required.",
                field="vendor",
                error_code="VENDOR_REQUIRED",
            )

        vendor = await self.user_service.get_user_by_public_id(property_dto.vendor_id, flush=True)

        
        duplicate_name = await self.property_service.get_by_vendor_and_name(
            vendor.id, property_dto.name, flush=True
        )
        if duplicate_name:
            raise AppException(
                status_code=409,
                message="A property with this name already exists for this vendor.",
                field="name",
                error_code="PROPERTY_NAME_EXIST",
            )

        base_slug = await generate_slug(property_dto.name)
        if not base_slug:
            raise AppException(
                status_code=422,
                message="Slug generation failed.",
                field="slug",
                error_code="SLUG_GENERATION_FAILED",
            )

        property_dto.slug = await self._generate_unique_slug(
            vendor.id, base_slug
        )
        if property_dto.city_id is None:
            raise AppException(
                status_code=422,
                message="city is required.",
                field="city",
                error_code="CITY_REQUIRED",
            )

        city = await self.city_service.get_by_public_id(property_dto.city_id, flush=True)
        if not city:
            raise AppException(
                status_code=404,
                message="City not found.",
                field="city",
                error_code="CITY_NOT_FOUND",
            )

        if property_dto.location_id is None:
            raise AppException(
                status_code=422,
                message="location is required.",
                field="location",
                error_code="LOCATION_REQUIRED",
            )

        location = await self.location_service.get_by_public_id(property_dto.location_id, flush=True)
        if not location:
            raise AppException(
                status_code=404,
                message="Location not found.",
                field="location",
                error_code="LOCATION_NOT_FOUND",
            )

        payload = Property(
            name=property_dto.name,
            slug=property_dto.slug,
            vendor_id=vendor.id,
            location_id=location.id,
            description=property_dto.description,
            city_id=city.id,
            type=property_dto.type,
            latitude=property_dto.latitude,
            longitude=property_dto.longitude,
            price_per_night=property_dto.price_per_night or property_dto.price or 0,
            sale_per_night=property_dto.sale_per_night or property_dto.sale_price,
            is_featured=property_dto.is_featured,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )

        created_property = await self.property_service.create(payload, commit=True)
        await self._sync_child_records(created_property.id, property_dto)
        return await self.property_service.get_by_public_id(
            created_property.public_id,
            with_relations={
                "vendor": True,
                "city": True,
                "location": True,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
                "property_food_options": True,
            },
            flush=True,
        ) or created_property

    

    async def _generate_unique_slug(self, vendor_id, base_slug: str) -> str:
        """
        WordPress-style slug uniqueness: if 'base_slug' is taken,
        try 'base_slug-2', 'base_slug-3', ... until a free one is found.
        """
        slug = base_slug
        suffix = 2

        while True:
            existing = await self.property_service.get_by_vendor_and_slug(
                vendor_id, slug, flush=True
            )
            if not existing:
                return slug

            slug = f"{base_slug}-{suffix}"
            suffix += 1

    async def _sync_child_records(self, property_id: int, property_dto: PropertyDTO) -> None:
        if property_dto.amenity_ids:
            for amenity_id in property_dto.amenity_ids:
                amenity = await self.amenity_service.get_by_public_id(amenity_id, flush=True)
                if not amenity:
                    raise AppException(
                        status_code=404,
                        message="Amenity not found.",
                        field="amenity_ids",
                        error_code="AMENITY_NOT_FOUND",
                    )
                await self.property_amenity_service.create(
                    PropertyAmenity(property_id=property_id, amenity_id=amenity.id),
                    commit=True,
                )

        if property_dto.facility_ids:
            for facility_id in property_dto.facility_ids:
                facility = await self.facility_service.get_by_public_id(facility_id, flush=True)
                if not facility:
                    raise AppException(
                        status_code=404,
                        message="Facility not found.",
                        field="facility_ids",
                        error_code="FACILITY_NOT_FOUND",
                    )
                await self.property_facility_service.create(
                    PropertyFacility(property_id=property_id, facility_id=facility.id),
                    commit=True,
                )

        if property_dto.food_option_ids:
            for food_name in property_dto.food_option_ids:
                await self.property_food_option_service.create(
                    PropertyFoodOption(
                        property_id=property_id,
                        name=food_name,
                        is_included=True,
                        status=PropertyFoodOptionStatus.ACTIVE,
                    ),
                    commit=True,
                )
