from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.property_food_option_model import PropertyFoodOption
from app.repositories.base_repository import BaseRepository, Page


class WithRelations(TypedDict, total=False):
    property: bool


class PropertyFoodOptionRepository(BaseRepository[PropertyFoodOption]):
    _relation_map = {
        "property": PropertyFoodOption.property,
    }
    _filter_map = {
        "property_id": PropertyFoodOption.property_id,
        "status": PropertyFoodOption.status,
        "is_included": PropertyFoodOption.is_included,
        "public_id": PropertyFoodOption.public_id,
    }

    async def create(
        self,
        property_food_option: PropertyFoodOption,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyFoodOption:
        self.db.add(property_food_option)
        if commit:
            await self.db.commit()
            await self.db.refresh(property_food_option)
        return property_food_option

    async def get_by_id(
        self,
        property_food_option_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyFoodOption]:
        query = self._apply_relations(
            select(PropertyFoodOption).where(PropertyFoodOption.id == property_food_option_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyFoodOption]:
        query = self._apply_relations(
            select(PropertyFoodOption).where(PropertyFoodOption.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyFoodOption]:
        query = self._apply_relations(
            select(PropertyFoodOption).where(PropertyFoodOption.property_id == property_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_all(query, flush=flush)

    async def update(
        self,
        property_food_option: PropertyFoodOption,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyFoodOption:
        if not commit:
            return property_food_option

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(PropertyFoodOption).where(PropertyFoodOption.id == property_food_option.id),
                with_relations,
                self._relation_map,
            )
            return await self._fetch_one(query)

        await self.db.refresh(property_food_option)
        return property_food_option

    async def delete(
        self,
        property_food_option: PropertyFoodOption,
        commit: bool = True,
    ) -> None:
        await self.db.delete(property_food_option)
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
    ) -> Page[PropertyFoodOption]:
        query = select(PropertyFoodOption).order_by(PropertyFoodOption.created_at.desc())
        query = self._apply_search(query, search, search_fields=[PropertyFoodOption.name, PropertyFoodOption.description])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)
