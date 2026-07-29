from app.repositories.location_repository import LocationRepository, WithRelations
from app.models.location_model import Location
from app.repositories.base_repository import Page
from typing import Optional

class LocationService:
    def __init__(
        self,
        location_repository : LocationRepository
    ):
        self.location_repository = location_repository

    
    async def create(
        self,
        location : Location,
        with_relations : Optional[WithRelations] = None,
        commit : bool = True
    ) -> Optional[Location]:
        return await self.location_repository.create(location, with_relations, commit)  


    async def get_by_name_and_city_id(
        self,
        name,
        city_id,
        flush,
    ) -> Optional[Location]:
         return await self.location_repository.get_by_name_and_city_id(
              name=name,
              city_id=city_id,
              flush=flush
         )

    async def get_by_id_with_city_country(
        self,
        location_id : str,
        flush
    ) -> Optional[Location]:

         return await self.location_repository.get_by_id_with_city_country(
              location_id=location_id,
              flush=flush
         )

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Location]:
        return await self.location_repository.get_by_public_id(
            public_id=public_id,
            with_relations=with_relations,
            flush=flush,
        )

    async def update(
        self,
        location: Location,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Optional[Location]:
        return await self.location_repository.update(
            location,
            with_relations=with_relations,
            commit=commit,
        )

    async def list(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False
    ) -> Page[Location]:
        return await self.location_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            with_relations=with_relations,
            flush=flush
        )
