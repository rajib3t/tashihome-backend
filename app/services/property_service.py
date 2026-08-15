from typing import Optional

from app.models.property_model import Property
from app.repositories.base_repository import Page
from app.repositories.property_repository import PropertyRepository, WithRelations


class PropertyService:
    def __init__(self, property_repository: PropertyRepository):
        self.property_repository = property_repository

    async def create(
        self,
        property_: Property,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Property:
        return await self.property_repository.create(property_, with_relations=with_relations, commit=commit)

    async def get_by_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Property]:
        return await self.property_repository.get_by_id(property_id, with_relations=with_relations, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Property]:
        return await self.property_repository.get_by_public_id(public_id, with_relations=with_relations, flush=flush)

    async def get_by_slug(
        self,
        slug: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Property]:
        return await self.property_repository.get_by_slug(slug, with_relations=with_relations, flush=flush)
    async def get_by_vendor_and_slug(
        self,
        vendor_id: int,
        slug: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Property]:
        return await self.property_repository.get_by_vendor_and_slug(
            vendor_id,
            slug,
            with_relations=with_relations,
            flush=flush,
        )

    async def get_by_vendor_and_name(
        self,
        vendor_id: int,
        name: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Property]:
        return await self.property_repository.get_by_vendor_and_name(
            vendor_id,
            name,
            with_relations=with_relations,
            flush=flush,
        )

    async def update(
        self,
        property_: Property,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Property:
        return await self.property_repository.update(property_, with_relations=with_relations, commit=commit)

    async def delete(
        self,
        property_: Property,
        commit: bool = True,
    ) -> None:
        await self.property_repository.delete(property_, commit=commit)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Page[Property]:
        return await self.property_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            with_relations=with_relations,
            flush=flush,
        )
