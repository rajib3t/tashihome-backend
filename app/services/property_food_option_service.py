from typing import Optional

from app.models.property_food_option_model import PropertyFoodOption
from app.repositories.base_repository import Page
from app.repositories.property_food_option_repository import PropertyFoodOptionRepository, WithRelations


class PropertyFoodOptionService:
    def __init__(self, property_food_option_repository: PropertyFoodOptionRepository):
        self.property_food_option_repository = property_food_option_repository

    async def create(
        self,
        property_food_option: PropertyFoodOption,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyFoodOption:
        return await self.property_food_option_repository.create(property_food_option, with_relations=with_relations, commit=commit)

    async def get_by_id(
        self,
        property_food_option_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyFoodOption]:
        return await self.property_food_option_repository.get_by_id(property_food_option_id, with_relations=with_relations, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyFoodOption]:
        return await self.property_food_option_repository.get_by_public_id(public_id, with_relations=with_relations, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyFoodOption]:
        return await self.property_food_option_repository.get_by_property_id(property_id, with_relations=with_relations, flush=flush)

    async def update(
        self,
        property_food_option: PropertyFoodOption,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyFoodOption:
        return await self.property_food_option_repository.update(property_food_option, with_relations=with_relations, commit=commit)

    async def delete(
        self,
        property_food_option: PropertyFoodOption,
        commit: bool = True,
    ) -> None:
        await self.property_food_option_repository.delete(property_food_option, commit=commit)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Page[PropertyFoodOption]:
        return await self.property_food_option_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            with_relations=with_relations,
            flush=flush,
        )
