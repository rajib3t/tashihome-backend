from typing import Optional
from app.models.city_model import City
from app.repositories.base_repository import Page
from app.repositories.city_repository import CityRepository, WithRelations

class CityService:
    def __init__(self, city_repository: CityRepository):
        self.city_repository = city_repository
    
    async def create(
        self, 
        city_data: City, 
        with_relations: Optional[WithRelations] = None,
        commit: bool = True 
    ) -> City:
        return await self.city_repository.create(
            city_data, 
            with_relations=with_relations,
            commit=commit
        )

    async def update(
        self,
        city_data: City,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> City:
        return await self.city_repository.update(
            city_data,
            with_relations=with_relations,
            commit=commit,
        )

    async def get_by_name(
        self,
        name: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[City]:
        return await self.city_repository.get_by_name(
            name,
            with_relations=with_relations,
            flush=flush
        )
    async def get_by_id(
        self,
        city_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[City]:
        return await self.city_repository.get_by_id(
            city_id,
            with_relations=with_relations,
            flush=flush
        )
    
    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[City]:
        return await self.city_repository.get_by_public_id(
            public_id,
            with_relations=with_relations,
            flush=flush
        )
        
    async def list(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False
    ) -> Page[City]:
        return await self.city_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            with_relations=with_relations,
            flush=flush
        )

    async def get_all(self) -> list[City]:
        return await self.city_repository.get_all()

