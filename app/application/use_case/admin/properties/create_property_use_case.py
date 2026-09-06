from app.application.use_case.base_use_case import BaseUseCase
from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin
from app.models.property_model import Property
from app.models.property_amenity_model import PropertyAmenity
from app.models.property_facility_model import PropertyFacility
from app.models.property_food_option_model import PropertyFoodOption, PropertyFoodOptionStatus
from app.models.property_room_type_model import PropertyRoomType
from app.models.property_room_type_price_model import PropertyRoomTypePrice
from app.services.city_service import CityService
from app.services.amenity_service import AmenityService
from app.services.facility_service import FacilityService
from app.services.property_amenity_service import PropertyAmenityService
from app.services.property_facility_service import PropertyFacilityService
from app.services.property_food_option_service import PropertyFoodOptionService
from app.services.property_room_type_service import PropertyRoomTypeService
from app.services.room_type_service import RoomTypeService
from app.services.location_service import LocationService
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService
from app.deps.auth import CurrentUser
from app.application.dto.properties.property import PropertyDTO
from typing import Optional
from app.core.exceptions import AppException
from app.services.user_service import UserService
from app.utils.slug import generate_slug


class CreatePropertyUseCase(PropertySerializerMixin, BaseUseCase):
    def __init__(
        self,
        property_service: PropertyService,
        user_service: UserService,
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
        self.user_service = user_service
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

    async def execute(self, property_dto: PropertyDTO) -> Optional[dict]:
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
            address=property_dto.address,
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
        full_property = await self.property_service.get_by_public_id(
            created_property.public_id,
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
        ) or created_property
        return await self.serialize_property(full_property)

    

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
        amenity_ids = property_dto.amenity_ids
        if amenity_ids is None and property_dto.amenities is not None:
            amenity_ids = [a.id for a in property_dto.amenities if getattr(a, "id", None)]

        if amenity_ids:
            for amenity_id in amenity_ids:
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

        facility_ids = property_dto.facility_ids
        if facility_ids is None:
            if property_dto.facility is not None:
                facility_ids = [f.id for f in property_dto.facility if getattr(f, "id", None)]
            elif property_dto.facilities is not None:
                facility_ids = [f.id for f in property_dto.facilities if getattr(f, "id", None)]

        if facility_ids:
            for facility_id in facility_ids:
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

        food_option_names = property_dto.food_option_ids
        if food_option_names is None and property_dto.food_options is not None:
            food_option_names = [fo.name for fo in property_dto.food_options if getattr(fo, "name", None)]

        if food_option_names:
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

        room_types_data = []
        if property_dto.room_types is not None:
            for rt in property_dto.room_types:
                rt_id = getattr(rt, "room_type_id", None) or getattr(rt, "id", None)
                if rt_id:
                    units = getattr(rt, "total_units", None)
                    units = units if units is not None else 1
                    price_per_night = getattr(rt, "price_per_night", None)
                    sale_per_night = getattr(rt, "sale_per_night", None)
                    pricing_tiers = getattr(rt, "pricing_tiers", None) or []
                    room_types_data.append({
                        "rt_id": rt_id,
                        "units": units,
                        "price_per_night": price_per_night,
                        "sale_per_night": sale_per_night,
                        "pricing_tiers": pricing_tiers,
                    })
        elif property_dto.room_type_ids is not None:
            for rt_id in property_dto.room_type_ids:
                if rt_id:
                    room_types_data.append({
                        "rt_id": rt_id,
                        "units": 1,
                        "price_per_night": None,
                        "sale_per_night": None,
                        "pricing_tiers": [],
                    })
        elif property_dto.room_type_id is not None:
            room_types_data.append({
                "rt_id": property_dto.room_type_id,
                "units": 1,
                "price_per_night": None,
                "sale_per_night": None,
                "pricing_tiers": [],
            })

        if room_types_data:
            for item in room_types_data:
                rt_id = item["rt_id"]
                units = item["units"]
                price_per_night = item["price_per_night"]
                sale_per_night = item["sale_per_night"]
                pricing_tiers = item["pricing_tiers"]

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
                        field="room_type_id",
                        error_code="ROOM_TYPE_NOT_FOUND",
                    )

                tier_objects = []
                seen_occupancies = set()
                for tier in pricing_tiers:
                    occ = getattr(tier, "occupancy", None) if hasattr(tier, "occupancy") else (tier.get("occupancy") if isinstance(tier, dict) else None)
                    t_price = getattr(tier, "price_per_night", None) if hasattr(tier, "price_per_night") else (tier.get("price_per_night") if isinstance(tier, dict) else None)
                    t_sale = getattr(tier, "sale_per_night", 0) if hasattr(tier, "sale_per_night") else (tier.get("sale_per_night", 0) if isinstance(tier, dict) else 0)

                    if occ is None or occ < 1:
                        raise AppException(
                            status_code=422,
                            message="Occupancy in pricing tiers must be greater than 0.",
                            field="pricing_tiers",
                            error_code="INVALID_TIER_OCCUPANCY",
                        )
                    if room_type.capacity and occ > room_type.capacity:
                        raise AppException(
                            status_code=422,
                            message=f"Occupancy {occ} cannot exceed room capacity of {room_type.capacity}.",
                            field="pricing_tiers",
                            error_code="TIER_OCCUPANCY_EXCEEDS_CAPACITY",
                        )
                    if occ in seen_occupancies:
                        raise AppException(
                            status_code=422,
                            message=f"Duplicate pricing tier for occupancy {occ}.",
                            field="pricing_tiers",
                            error_code="DUPLICATE_TIER_OCCUPANCY",
                        )
                    seen_occupancies.add(occ)
                    tier_objects.append(
                        PropertyRoomTypePrice(
                            occupancy=occ,
                            price_per_night=t_price or 0,
                            sale_per_night=t_sale or 0,
                        )
                    )

                await self.property_room_type_service.create(
                    PropertyRoomType(
                        property_id=property_id,
                        room_type_id=room_type.id,
                        total_units=units,
                        price_per_night=price_per_night,
                        sale_per_night=sale_per_night,
                        pricing_tiers=tier_objects,
                    ),
                    commit=True,
                )
