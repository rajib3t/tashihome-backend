from typing import Optional

from app.models.property_amenity_model import PropertyAmenity
from app.repositories.base_repository import Page
from app.repositories.property_amenity_repository import PropertyAmenityRepository, WithRelations


class PropertyAmenityService:
    def __init__(self, property_amenity_repository: PropertyAmenityRepository):
        self.property_amenity_repository = property_amenity_repository

    async def create(
        self,
        property_amenity: PropertyAmenity,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyAmenity:
        return await self.property_amenity_repository.create(property_amenity, with_relations=with_relations, commit=commit)

    async def get_by_id(
        self,
        property_amenity_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyAmenity]:
        return await self.property_amenity_repository.get_by_id(property_amenity_id, with_relations=with_relations, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyAmenity]:
        return await self.property_amenity_repository.get_by_public_id(public_id, with_relations=with_relations, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyAmenity]:
        return await self.property_amenity_repository.get_by_property_id(property_id, with_relations=with_relations, flush=flush)

    async def update(
        self,
        property_amenity: PropertyAmenity,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyAmenity:
        return await self.property_amenity_repository.update(property_amenity, with_relations=with_relations, commit=commit)

    async def delete(
        self,
        property_amenity: PropertyAmenity,
        commit: bool = True,
    ) -> None:
        await self.property_amenity_repository.delete(property_amenity, commit=commit)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Page[PropertyAmenity]:
        return await self.property_amenity_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            with_relations=with_relations,
            flush=flush,
        )
