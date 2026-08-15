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
