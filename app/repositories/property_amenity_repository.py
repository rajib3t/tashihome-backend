from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.property_amenity_model import PropertyAmenity
from app.repositories.base_repository import BaseRepository, Page


class WithRelations(TypedDict, total=False):
    property: bool
    amenity: bool


class PropertyAmenityRepository(BaseRepository[PropertyAmenity]):
    _relation_map = {
        "property": PropertyAmenity.property,
        "amenity": PropertyAmenity.amenity,
    }
    _filter_map = {
        "property_id": PropertyAmenity.property_id,
        "amenity_id": PropertyAmenity.amenity_id,
        "public_id": PropertyAmenity.public_id,
    }

    async def create(
        self,
        property_amenity: PropertyAmenity,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyAmenity:
        self.db.add(property_amenity)
        if commit:
            await self.db.commit()
            await self.db.refresh(property_amenity)
        return property_amenity

    async def get_by_id(
        self,
        property_amenity_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyAmenity]:
        query = self._apply_relations(
            select(PropertyAmenity).where(PropertyAmenity.id == property_amenity_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyAmenity]:
        query = self._apply_relations(
            select(PropertyAmenity).where(PropertyAmenity.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyAmenity]:
        query = self._apply_relations(
            select(PropertyAmenity).where(PropertyAmenity.property_id == property_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_all(query, flush=flush)

    async def update(
        self,
        property_amenity: PropertyAmenity,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyAmenity:
        if not commit:
            return property_amenity

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(PropertyAmenity).where(PropertyAmenity.id == property_amenity.id),
                with_relations,
                self._relation_map,
            )
            return await self._fetch_one(query)

        await self.db.refresh(property_amenity)
        return property_amenity

    async def delete(
        self,
        property_amenity: PropertyAmenity,
        commit: bool = True,
    ) -> None:
        await self.db.delete(property_amenity)
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
    ) -> Page[PropertyAmenity]:
        query = select(PropertyAmenity).order_by(PropertyAmenity.created_at.desc())
        query = self._apply_search(query, search, search_fields=[PropertyAmenity.notes])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)
