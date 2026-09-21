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
from app.models.property_room_type_price_model import PropertyRoomTypePrice
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


class VendorUpdatePropertyUseCase(PropertySerializerMixin, BaseUseCase):
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

    async def execute(self, property_id: str, data: PropertyUpdateDTO) -> dict:
        existing_property = await self.property_service.get_by_public_id(property_id, flush=False)
        if not existing_property:
            raise AppException(
                status_code=404,
                message="Property not found.",
                field="property_id",
                error_code="PROPERTY_NOT_FOUND",
            )

        # Ownership check — vendor can only update their own properties
        if existing_property.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You are not authorized to update this property.",
                field="property_id",
                error_code="PROPERTY_ACCESS_DENIED",
            )

        if data.name is not None:
            normalized_name = data.name.strip()
            duplicate_name = await self.property_service.get_by_vendor_and_name(
                existing_property.vendor_id, normalized_name, flush=True
            )
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
            duplicate_slug = await self.property_service.get_by_vendor_and_slug(
                existing_property.vendor_id, normalized_slug, flush=True
            )
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

        if data.price_per_night and data.price_per_night > 0 and data.sale_per_night is not None and data.sale_per_night > data.price_per_night:
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
        if data.type is not None:
            existing_property.type = data.type

        # is_featured and status are admin-only fields; vendors cannot change them

        existing_property.updated_by = self.current_user.id
        updated_property = await self.property_service.update(existing_property)
        db = getattr(getattr(self.property_service, "property_repository", None), "db", None)
        updated_property = await self.property_service.update(existing_property, commit=False if db is not None else True)
        await self._sync_child_records(updated_property.id, data)

        if db is not None and hasattr(db, "commit"):
            await db.commit()

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
        amenity_ids = data.amenity_ids
        if amenity_ids is None and data.amenities is not None:
            amenity_ids = [a.id for a in data.amenities if getattr(a, "id", None)]

        if amenity_ids is not None:
            existing_amenities = await self.property_amenity_service.get_by_property_id(property_id, with_relations={"amenity": True}, flush=False)
            existing_amenity_ids = {
                str(getattr(item.amenity, "public_id", None) or getattr(item, "amenity_id", None))
                for item in existing_amenities
            }
            incoming_amenity_ids = {str(aid).strip() for aid in amenity_ids if str(aid).strip()}

            if existing_amenity_ids != incoming_amenity_ids:
                if hasattr(self.property_amenity_service, "delete_by_property_id"):
                    await self.property_amenity_service.delete_by_property_id(property_id, commit=False)
                else:
                    for item in existing_amenities:
                        await self.property_amenity_service.delete(item, commit=False)

                amenities_map = {}
                if hasattr(self.amenity_service, "get_by_public_ids"):
                    found = await self.amenity_service.get_by_public_ids(list(incoming_amenity_ids), flush=True)
                    for a in found:
                        amenities_map[str(a.public_id)] = a

                amenity_records = []
                for aid in incoming_amenity_ids:
                    amenity = amenities_map.get(aid)
                    if not amenity:
                        amenity = await self.amenity_service.get_by_public_id(aid, flush=True)
                    if not amenity:
                        raise AppException(
                            status_code=404,
                            message="Amenity not found.",
                            field="amenities",
                            error_code="AMENITY_NOT_FOUND",
                        )
                    amenity_records.append(PropertyAmenity(property_id=property_id, amenity_id=amenity.id))

                if amenity_records:
                    if hasattr(self.property_amenity_service, "create_many"):
                        await self.property_amenity_service.create_many(amenity_records, commit=False)
                    else:
                        for item in amenity_records:
                            await self.property_amenity_service.create(item, commit=False)

        facility_ids = data.facility_ids
        if facility_ids is None:
            if data.facility is not None:
                facility_ids = [f.id for f in data.facility if getattr(f, "id", None)]
            elif data.facilities is not None:
                facility_ids = [f.id for f in data.facilities if getattr(f, "id", None)]

        if facility_ids is not None:
            existing_facilities = await self.property_facility_service.get_by_property_id(property_id, with_relations={"facility": True}, flush=False)
            existing_facility_ids = {
                str(getattr(item.facility, "public_id", None) or getattr(item, "facility_id", None))
                for item in existing_facilities
            }
            incoming_facility_ids = {str(fid).strip() for fid in facility_ids if str(fid).strip()}

            if existing_facility_ids != incoming_facility_ids:
                if hasattr(self.property_facility_service, "delete_by_property_id"):
                    await self.property_facility_service.delete_by_property_id(property_id, commit=False)
                else:
                    for item in existing_facilities:
                        await self.property_facility_service.delete(item, commit=False)

                facilities_map = {}
                if hasattr(self.facility_service, "get_by_public_ids"):
                    found = await self.facility_service.get_by_public_ids(list(incoming_facility_ids), flush=True)
                    for f in found:
                        facilities_map[str(f.public_id)] = f

                facility_records = []
                for fid in incoming_facility_ids:
                    facility = facilities_map.get(fid)
                    if not facility:
                        facility = await self.facility_service.get_by_public_id(fid, flush=True)
                    if not facility:
                        raise AppException(
                            status_code=404,
                            message="Facility not found.",
                            field="facility",
                            error_code="FACILITY_NOT_FOUND",
                        )
                    facility_records.append(PropertyFacility(property_id=property_id, facility_id=facility.id))

                if facility_records:
                    if hasattr(self.property_facility_service, "create_many"):
                        await self.property_facility_service.create_many(facility_records, commit=False)
                    else:
                        for item in facility_records:
                            await self.property_facility_service.create(item, commit=False)

        food_option_names = data.food_option_ids
        if food_option_names is None and data.food_options is not None:
            food_option_names = [fo.name for fo in data.food_options if getattr(fo, "name", None)]

        if food_option_names is not None:
            existing_food_options = await self.property_food_option_service.get_by_property_id(property_id, flush=False)
            existing_food_names = {item.name for item in existing_food_options}
            incoming_food_names = {str(fn).strip() for fn in food_option_names if str(fn).strip()}

            if existing_food_names != incoming_food_names:
                if hasattr(self.property_food_option_service, "delete_by_property_id"):
                    await self.property_food_option_service.delete_by_property_id(property_id, commit=False)
                else:
                    for item in existing_food_options:
                        await self.property_food_option_service.delete(item, commit=False)

                food_records = [
                    PropertyFoodOption(
                        property_id=property_id,
                        name=food_name,
                        is_included=True,
                        status=PropertyFoodOptionStatus.ACTIVE,
                    )
                    for food_name in incoming_food_names
                ]
                if food_records:
                    if hasattr(self.property_food_option_service, "create_many"):
                        await self.property_food_option_service.create_many(food_records, commit=False)
                    else:
                        for item in food_records:
                            await self.property_food_option_service.create(item, commit=False)

        room_types_data = None
        if data.room_types is not None:
            room_types_data = []
            for rt in data.room_types:
                rt_room_type = getattr(rt, "room_type", None)
                rt_id = (
                    getattr(rt, "room_type_id", None)
                    or (rt_room_type.get("id") or rt_room_type.get("public_id") if isinstance(rt_room_type, dict) else None)
                    or (getattr(rt_room_type, "id", None) or getattr(rt_room_type, "public_id", None) if rt_room_type else None)
                    or getattr(rt, "id", None)
                )
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
        elif data.room_type_ids is not None:
            room_types_data = [
                {
                    "rt_id": rt_id,
                    "units": 1,
                    "price_per_night": None,
                    "sale_per_night": None,
                    "pricing_tiers": [],
                }
                for rt_id in data.room_type_ids
                if rt_id
            ]
        elif data.room_type_id is not None:
            room_types_data = [
                {
                    "rt_id": data.room_type_id,
                    "units": 1,
                    "price_per_night": None,
                    "sale_per_night": None,
                    "pricing_tiers": [],
                }
            ]

        if room_types_data is not None:
            existing_room_types = await self.property_room_type_service.get_by_property_id(property_id, flush=False)
            if hasattr(self.property_room_type_service, "delete_by_property_id"):
                await self.property_room_type_service.delete_by_property_id(property_id, commit=False)
            else:
                for item in existing_room_types:
                    await self.property_room_type_service.delete(item, commit=False)

            rt_id_strs = [str(item["rt_id"]).strip() for item in room_types_data if str(item["rt_id"]).strip()]
            room_types_map = {}
            if hasattr(self.room_type_service, "get_by_public_ids"):
                found_rts = await self.room_type_service.get_by_public_ids(rt_id_strs, flush=True)
                for rt in found_rts:
                    room_types_map[str(rt.public_id)] = rt

            rt_records = []
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
                room_type = room_types_map.get(str(rt_id))
                if not room_type:
                    room_type = await self.room_type_service.get_by_public_id(rt_id, flush=True)
                if not room_type:
                    prop_rt = await self.property_room_type_service.get_by_public_id(rt_id, with_relations={"room_type": True}, flush=True)
                    if prop_rt and prop_rt.room_type:
                        room_type = prop_rt.room_type
                if not room_type:
                    raise AppException(
                        status_code=404,
                        message="Room type not found.",
                        field="room_type_ids",
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

                rt_records.append(
                    PropertyRoomType(
                        property_id=property_id,
                        room_type_id=room_type.id,
                        total_units=units,
                        price_per_night=price_per_night,
                        sale_per_night=sale_per_night,
                        pricing_tiers=tier_objects,
                    )
                )

            if rt_records:
                if hasattr(self.property_room_type_service, "create_many"):
                    await self.property_room_type_service.create_many(rt_records, commit=False)
                else:
                    for r in rt_records:
                        await self.property_room_type_service.create(r, commit=False)


