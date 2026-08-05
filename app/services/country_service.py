from typing import Optional

from app.models.country_model import Country
from app.repositories.base_repository import Page
from app.repositories.country_repository import CountryRepository, WithRelations


class CountryService:
    def __init__(
            self, 
            country_repository: CountryRepository
        ):
        self._country_repository = country_repository


    async def get_country_by_id(
            self, 
            country_id: int, 
            with_relations: Optional[WithRelations] = None, 
            flush: bool = False
        ) -> Optional[Country]:
        return await self._country_repository.get_by_id(
            country_id, 
            with_relations=with_relations, 
            flush=flush
        )
    
    async def get_by_public_id(
            self, 
            public_id: str, 
            with_relations: Optional[WithRelations] = None, 
            flush: bool = False
        ) -> Optional[Country]:
        return await self._country_repository.get_by_public_id(
            public_id, 
            with_relations=with_relations, 
            flush=flush
        )
    
    async def get_by_name(
            self, 
            name: str, 
            with_relations: Optional[WithRelations] = None, 
            flush: bool = False
        ) -> Optional[Country]:
        return await self._country_repository.get_by_name(
            name, 
            with_relations=with_relations, 
            flush=flush
        )
    
    async def get_by_code(
            self,
            code:str,
            with_relations: Optional[WithRelations] = None,
            flush: bool = False
    ) -> Optional[Country]:
        return await self._country_repository.get_by_code(
            code,
            with_relations=with_relations,
            flush=flush
        )
    
    async def create_country(
            self, 
            country: Country, 
            with_relations: Optional[WithRelations] = None, 
            commit: bool = True
        ) -> Country:
        return await self._country_repository.create(
            country, 
            with_relations=with_relations, 
            commit=commit
        )
    
    async def update_country(
            self, 
            country: Country, 
            with_relations: Optional[WithRelations] = None, 
            commit: bool = True
        ) -> Country:
        return await self._country_repository.update(
            country, 
            with_relations=with_relations, 
            commit=commit
        )
    
    async def delete_country(
            self, 
            country: Country, 
            commit: bool = True
        ) -> None:
        await self._country_repository.delete(
            country, 
            commit=commit
        )
    
    async def list(
            self,
            page: int = 1,
            page_size: int = 10,
            search: Optional[str] = None,
            filters: Optional[list[dict[str, str]]] = None,
            with_relations: Optional[WithRelations] = None,
            flush: bool = False
        ) -> Page[Country]:
        return await self._country_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            with_relations=with_relations,
            flush=flush
        )

    async def get_all(self) -> list[Country]:
        return await self._country_repository.get_all()

