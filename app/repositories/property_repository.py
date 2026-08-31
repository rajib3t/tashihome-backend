from typing import Optional, TypedDict

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.property_amenity_model import PropertyAmenity
from app.models.property_facility_model import PropertyFacility
from app.models.property_room_type_model import PropertyRoomType
from app.models.property_model import Property
from app.repositories.base_repository import BaseRepository, Page


class WithRelations(TypedDict, total=False):
    vendor: bool
    location: bool
    city: bool
    property_room_types: bool
    property_assets: bool
    property_facilities: bool
    property_amenities: bool
    property_food_options: bool


class PropertyRepository(BaseRepository[Property]):
    @property
    def _relation_map(self):
        from app.models.property_amenity_model import PropertyAmenity
        from app.models.property_facility_model import PropertyFacility
        from app.models.property_room_type_model import PropertyRoomType
        return {
            "vendor": Property.vendor,
            "location": Property.location,
            "city": Property.city,
            "property_room_types": selectinload(Property.property_room_types).selectinload(PropertyRoomType.room_type),
            "property_assets": selectinload(Property.property_assets),
            "property_facilities": selectinload(Property.property_facilities).selectinload(PropertyFacility.facility),
            "property_amenities": selectinload(Property.property_amenities).selectinload(PropertyAmenity.amenity),
            "property_food_options": selectinload(Property.property_food_options),
        }

    _filter_map = {

        "name": Property.name,
        "slug": Property.slug,
        "status": Property.status,
        "vendor_id": Property.vendor_id,
        "location_id": Property.location_id,
        "city_id": Property.city_id,
        "public_id": Property.public_id,
        "is_featured": Property.is_featured,
    }

    async def create(
        self,
        property_: Property,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Property:
        self.db.add(property_)
        if commit:
            await self.db.commit()
            await self.db.refresh(property_)
        return property_

    async def get_by_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Property]:
        query = self._apply_relations(
            select(Property).where(Property.id == property_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Property]:
        query = self._apply_relations(
            select(Property).where(Property.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)
    async def get_by_slug(
            self,
            slug: str,
            with_relations: Optional[WithRelations] = None,
            flush: bool = False,
        ) -> Optional[Property]:
            query = self._apply_relations(
                select(Property).where(Property.slug == slug),
                with_relations,
                self._relation_map,
            )
            return await self._fetch_one(query, flush=flush)
    async def get_by_vendor_and_slug(
        self,
        vendor_id: int,
        slug: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Property]:
        query = self._apply_relations(
            select(Property).where(Property.vendor_id == vendor_id, Property.slug.ilike(slug.strip())),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)


    async def get_by_vendor_and_name(
        self,
        vendor_id: int,
        name: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Property]:
        query = self._apply_relations(
            select(Property).where(Property.vendor_id == vendor_id, Property.name.ilike(name.strip())),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def update(
        self,
        property_: Property,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Property:
        if not commit:
            return property_

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(Property).where(Property.id == property_.id),
                with_relations,
                self._relation_map,
            )
            return await self._fetch_one(query)

        await self.db.refresh(property_)
        return property_

    async def delete(
        self,
        property_: Property,
        commit: bool = True,
    ) -> None:
        await self.db.delete(property_)
        if commit:
            await self.db.commit()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Page[Property]:
        query = select(Property).order_by(Property.created_at.desc())
        query = self._apply_search(query, search, search_fields=[Property.name, Property.slug, Property.description])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def get_all_by_vendor(self, vendor_id: int) -> list[Property]:
        query = select(Property).where(Property.vendor_id == vendor_id)
        return await self._fetch_all(query)

    async def search_stays(
        self,
        region: Optional[str] = None,
        city_name: Optional[str] = None,
        location_name: Optional[str] = None,
        country_name: Optional[str] = None,
        city_id: Optional[int | str] = None,
        location_id: Optional[int | str] = None,
        country_id: Optional[int | str] = None,
        check_in_date: Optional[Any] = None,
        check_out_date: Optional[Any] = None,
        guests: Optional[int] = None,
        rooms: int = 1,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        property_type: Optional[str] = None,
        is_featured: Optional[bool] = None,
        amenity_ids: Optional[list[int | str]] = None,
        facility_ids: Optional[list[int | str]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Page[Property]:
        from app.models.city_model import City
        from app.models.country_model import Country
        from app.models.location_model import Location
        from app.models.property_model import PropertyStatus, PropertyType
        from app.models.property_room_type_model import PropertyRoomType
        from app.models.room_type_model import RoomType
        from app.models.booking_model import Booking, BookingStatus
        from app.models.room_block_model import RoomBlock
        from app.models.property_amenity_model import PropertyAmenity
        from app.models.property_facility_model import PropertyFacility
        from app.models.amenity_model import Amenity
        from app.models.facility_model import Facility
        from sqlalchemy import and_, or_, func, case, distinct

        query = select(Property).where(Property.status == PropertyStatus.ACTIVE)

        # Outer join City, Location, Country for text and location filtering
        query = query.outerjoin(City, Property.city_id == City.id)
        query = query.outerjoin(Location, Property.location_id == Location.id)
        query = query.outerjoin(Country, City.country_id == Country.id)

        # 1. Text / Region search
        if region and region.strip():
            term = f"%{region.strip()}%"
            query = query.where(
                or_(
                    Property.name.ilike(term),
                    Property.slug.ilike(term),
                    Property.address.ilike(term),
                    Property.description.ilike(term),
                    City.name.ilike(term),
                    Location.name.ilike(term),
                    Country.name.ilike(term),
                )
            )

        # 2. City name filter
        if city_name and city_name.strip():
            query = query.where(City.name.ilike(f"%{city_name.strip()}%"))

        # 3. Location name filter
        if location_name and location_name.strip():
            query = query.where(Location.name.ilike(f"%{location_name.strip()}%"))

        # 4. Country name filter
        if country_name and country_name.strip():
            query = query.where(Country.name.ilike(f"%{country_name.strip()}%"))

        # 5. ID filters (city_id, location_id, country_id)
        if city_id is not None:
            if isinstance(city_id, int) or (isinstance(city_id, str) and city_id.isdigit()):
                query = query.where(Property.city_id == int(city_id))
            else:
                query = query.where(City.public_id == city_id)

        if location_id is not None:
            if isinstance(location_id, int) or (isinstance(location_id, str) and location_id.isdigit()):
                query = query.where(Property.location_id == int(location_id))
            else:
                query = query.where(Location.public_id == location_id)

        if country_id is not None:
            if isinstance(country_id, int) or (isinstance(country_id, str) and country_id.isdigit()):
                query = query.where(City.country_id == int(country_id))
            else:
                query = query.where(Country.public_id == country_id)

        # 6. Featured filter
        if is_featured is not None:
            query = query.where(Property.is_featured == is_featured)

        # 7. Property type filter
        if property_type:
            try:
                pt_enum = PropertyType(property_type)
                query = query.where(Property.type == pt_enum)
            except ValueError:
                query = query.where(func.lower(Property.type) == property_type.lower())

        # 8. Price filter (effective price = sale_per_night if > 0 else price_per_night)
        effective_price = case(
            (and_(Property.sale_per_night.isnot(None), Property.sale_per_night > 0), Property.sale_per_night),
            else_=Property.price_per_night,
        )
        if min_price is not None:
            query = query.where(effective_price >= min_price)
        if max_price is not None:
            query = query.where(effective_price <= max_price)

        # 9. Amenities filter
        if amenity_ids:
            for a_id in amenity_ids:
                if str(a_id).isdigit():
                    query = query.where(
                        Property.id.in_(
                            select(PropertyAmenity.property_id).where(PropertyAmenity.amenity_id == int(a_id))
                        )
                    )
                else:
                    query = query.where(
                        Property.id.in_(
                            select(PropertyAmenity.property_id)
                            .join(Amenity, PropertyAmenity.amenity_id == Amenity.id)
                            .where(Amenity.public_id == a_id)
                        )
                    )

        # 10. Facilities filter
        if facility_ids:
            for f_id in facility_ids:
                if str(f_id).isdigit():
                    query = query.where(
                        Property.id.in_(
                            select(PropertyFacility.property_id).where(PropertyFacility.facility_id == int(f_id))
                        )
                    )
                else:
                    query = query.where(
                        Property.id.in_(
                            select(PropertyFacility.property_id)
                            .join(Facility, PropertyFacility.facility_id == Facility.id)
                            .where(Facility.public_id == f_id)
                        )
                    )

        # 11. Guests / Capacity filter
        if guests is not None and guests > 0:
            # Match properties where at least one room type can accommodate guests OR total capacity across property >= guests
            capacity_condition = or_(
                Property.id.in_(
                    select(PropertyRoomType.property_id)
                    .join(RoomType, PropertyRoomType.room_type_id == RoomType.id)
                    .where(RoomType.capacity >= guests)
                ),
                Property.id.in_(
                    select(PropertyRoomType.property_id)
                    .join(RoomType, PropertyRoomType.room_type_id == RoomType.id)
                    .group_by(PropertyRoomType.property_id)
                    .having(func.sum(RoomType.capacity * PropertyRoomType.total_units) >= guests)
                ),
                # If property has no room types registered, allow default
                Property.id.not_in(select(PropertyRoomType.property_id))
            )
            query = query.where(capacity_condition)

        # 12. Date Availability filter
        if check_in_date and check_out_date:
            # Exclude properties whose available units for requested period is less than requested rooms
            # Booked units overlapping [check_in_date, check_out_date)
            booked_subq = (
                select(
                    Booking.property_id,
                    func.coalesce(func.sum(Booking.num_rooms), 0).label("booked_count")
                )
                .where(
                    Booking.status.not_in([BookingStatus.CANCELLED, BookingStatus.NO_SHOW]),
                    Booking.check_in_date < check_out_date,
                    Booking.check_out_date > check_in_date,
                )
                .group_by(Booking.property_id)
                .subquery()
            )

            # Blocked units overlapping [check_in_date, check_out_date)
            blocked_subq = (
                select(
                    RoomBlock.property_id,
                    func.coalesce(func.sum(RoomBlock.units_blocked), 0).label("blocked_count")
                )
                .where(
                    RoomBlock.block_start_date < check_out_date,
                    RoomBlock.block_end_date > check_in_date,
                )
                .group_by(RoomBlock.property_id)
                .subquery()
            )

            # Total units configured per property
            total_units_subq = (
                select(
                    PropertyRoomType.property_id,
                    func.coalesce(func.sum(PropertyRoomType.total_units), 1).label("total_units")
                )
                .group_by(PropertyRoomType.property_id)
                .subquery()
            )

            # Join subqueries
            query = query.outerjoin(total_units_subq, Property.id == total_units_subq.c.property_id)
            query = query.outerjoin(booked_subq, Property.id == booked_subq.c.property_id)
            query = query.outerjoin(blocked_subq, Property.id == blocked_subq.c.property_id)

            calc_total = func.coalesce(total_units_subq.c.total_units, 1)
            calc_booked = func.coalesce(booked_subq.c.booked_count, 0)
            calc_blocked = func.coalesce(blocked_subq.c.blocked_count, 0)
            avail_units = calc_total - (calc_booked + calc_blocked)

            query = query.where(avail_units >= rooms)

        # 13. Sorting
        sort_by_lower = sort_by.lower()
        if sort_by_lower in ["price_asc", "price_low_to_high"]:
            query = query.order_by(effective_price.asc())
        elif sort_by_lower in ["price_desc", "price_high_to_low"]:
            query = query.order_by(effective_price.desc())
        elif sort_by_lower == "price":
            query = query.order_by(effective_price.asc() if sort_order.lower() == "asc" else effective_price.desc())
        elif sort_by_lower == "name":
            query = query.order_by(Property.name.asc() if sort_order.lower() == "asc" else Property.name.desc())
        else:
            # Default: created_at
            query = query.order_by(Property.created_at.desc() if sort_order.lower() == "desc" else Property.created_at.asc())

        # 14. Eager-load relations and paginate
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)
