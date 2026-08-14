from typing import Optional

from app.models.property_asset_model import PropertyAsset, PropertyAssetUseFor
from app.repositories.base_repository import Page
from app.repositories.property_asset_repository import PropertyAssetRepository, WithRelations


class PropertyAssetService:
    def __init__(self, property_asset_repository: PropertyAssetRepository):
        self.property_asset_repository = property_asset_repository

    async def create(
        self,
        property_asset: PropertyAsset,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyAsset:
        return await self.property_asset_repository.create(property_asset, with_relations=with_relations, commit=commit)

    async def get_by_id(
        self,
        property_asset_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyAsset]:
        return await self.property_asset_repository.get_by_id(property_asset_id, with_relations=with_relations, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyAsset]:
        return await self.property_asset_repository.get_by_public_id(public_id, with_relations=with_relations, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyAsset]:
        return await self.property_asset_repository.get_by_property_id(property_id, with_relations=with_relations, flush=flush)

    async def get_by_property_id_and_use_for(
        self,
        property_id: int,
        use_for: PropertyAssetUseFor,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyAsset]:
        return await self.property_asset_repository.get_by_property_id_and_use_for(property_id, use_for, with_relations=with_relations, flush=flush)

    async def update(
        self,
        property_asset: PropertyAsset,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyAsset:
        return await self.property_asset_repository.update(property_asset, with_relations=with_relations, commit=commit)

    async def delete(
        self,
        property_asset: PropertyAsset,
        commit: bool = True,
    ) -> None:
        await self.property_asset_repository.delete(property_asset, commit=commit)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Page[PropertyAsset]:
        return await self.property_asset_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            with_relations=with_relations,
            flush=flush,
        )
