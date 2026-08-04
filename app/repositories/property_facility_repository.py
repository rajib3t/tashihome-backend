from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.property_facility_model import PropertyFacility
from app.repositories.base_repository import BaseRepository, Page


class WithRelations(TypedDict, total=False):
    property: bool
    facility: bool


class PropertyFacilityRepository(BaseRepository[PropertyFacility]):
    _relation_map = {
        "property": PropertyFacility.property,
        "facility": PropertyFacility.facility,
    }
    _filter_map = {
        "property_id": PropertyFacility.property_id,
        "facility_id": PropertyFacility.facility_id,
        "public_id": PropertyFacility.public_id,
    }

    async def create(
        self,
        property_facility: PropertyFacility,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyFacility:
        self.db.add(property_facility)
        if commit:
            await self.db.commit()
            await self.db.refresh(property_facility)
        return property_facility

    async def get_by_id(
        self,
        property_facility_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyFacility]:
        query = self._apply_relations(
            select(PropertyFacility).where(PropertyFacility.id == property_facility_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyFacility]:
        query = self._apply_relations(
            select(PropertyFacility).where(PropertyFacility.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyFacility]:
        query = self._apply_relations(
            select(PropertyFacility).where(PropertyFacility.property_id == property_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_all(query, flush=flush)

    async def update(
        self,
        property_facility: PropertyFacility,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyFacility:
        if not commit:
            return property_facility

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(PropertyFacility).where(PropertyFacility.id == property_facility.id),
                with_relations,
                self._relation_map,
            )
            return await self._fetch_one(query)

        await self.db.refresh(property_facility)
        return property_facility

    async def delete(
        self,
        property_facility: PropertyFacility,
        commit: bool = True,
    ) -> None:
        await self.db.delete(property_facility)
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
    ) -> Page[PropertyFacility]:
        query = select(PropertyFacility).order_by(PropertyFacility.created_at.desc())
        query = self._apply_search(query, search, search_fields=[PropertyFacility.notes])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)
