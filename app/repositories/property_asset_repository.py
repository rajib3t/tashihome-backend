from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.property_asset_model import PropertyAsset
from app.repositories.base_repository import BaseRepository, Page


class WithRelations(TypedDict, total=False):
    property: bool


class PropertyAssetRepository(BaseRepository[PropertyAsset]):
    _relation_map = {
        "property": PropertyAsset.property,
    }
    _filter_map = {
        "property_id": PropertyAsset.property_id,
        "asset_type": PropertyAsset.asset_type,
        "status": PropertyAsset.status,
        "is_primary": PropertyAsset.is_primary,
        "public_id": PropertyAsset.public_id,
    }

    async def create(
        self,
        property_asset: PropertyAsset,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyAsset:
        self.db.add(property_asset)
        if commit:
            await self.db.commit()
            await self.db.refresh(property_asset)
        return property_asset

    async def get_by_id(
        self,
        property_asset_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyAsset]:
        query = self._apply_relations(
            select(PropertyAsset).where(PropertyAsset.id == property_asset_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyAsset]:
        query = self._apply_relations(
            select(PropertyAsset).where(PropertyAsset.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyAsset]:
        query = self._apply_relations(
            select(PropertyAsset).where(PropertyAsset.property_id == property_id).order_by(PropertyAsset.sort_order.asc(), PropertyAsset.created_at.desc()),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_all(query, flush=flush)

    async def update(
        self,
        property_asset: PropertyAsset,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyAsset:
        if not commit:
            return property_asset

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(PropertyAsset).where(PropertyAsset.id == property_asset.id),
                with_relations,
                self._relation_map,
            )
            return await self._fetch_one(query)

        await self.db.refresh(property_asset)
        return property_asset

    async def delete(
        self,
        property_asset: PropertyAsset,
        commit: bool = True,
    ) -> None:
        await self.db.delete(property_asset)
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
    ) -> Page[PropertyAsset]:
        query = select(PropertyAsset).order_by(PropertyAsset.created_at.desc())
        query = self._apply_search(query, search, search_fields=[PropertyAsset.title, PropertyAsset.file_url])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)
