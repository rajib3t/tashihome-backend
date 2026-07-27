from typing import Optional
from app.models.city_model import City
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
        
        
    