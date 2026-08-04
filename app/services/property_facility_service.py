from typing import Optional

from app.models.property_facility_model import PropertyFacility
from app.repositories.base_repository import Page
from app.repositories.property_facility_repository import PropertyFacilityRepository, WithRelations


class PropertyFacilityService:
    def __init__(self, property_facility_repository: PropertyFacilityRepository):
        self.property_facility_repository = property_facility_repository

    async def create(
        self,
        property_facility: PropertyFacility,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyFacility:
        return await self.property_facility_repository.create(property_facility, with_relations=with_relations, commit=commit)

    async def get_by_id(
        self,
        property_facility_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyFacility]:
        return await self.property_facility_repository.get_by_id(property_facility_id, with_relations=with_relations, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyFacility]:
        return await self.property_facility_repository.get_by_public_id(public_id, with_relations=with_relations, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyFacility]:
        return await self.property_facility_repository.get_by_property_id(property_id, with_relations=with_relations, flush=flush)

    async def update(
        self,
        property_facility: PropertyFacility,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyFacility:
        return await self.property_facility_repository.update(property_facility, with_relations=with_relations, commit=commit)

    async def delete(
        self,
        property_facility: PropertyFacility,
        commit: bool = True,
    ) -> None:
        await self.property_facility_repository.delete(property_facility, commit=commit)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Page[PropertyFacility]:
        return await self.property_facility_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            with_relations=with_relations,
            flush=flush,
        )
