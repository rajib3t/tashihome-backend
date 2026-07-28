from sqlalchemy import select
from typing import Optional
from app.repositories.base_repository import BaseRepository, Page
from app.models.city_model import City
from typing import TypedDict

class WithRelations(TypedDict, total=False):
    country: bool
    
class CityRepository(BaseRepository[City]):
    _relation_map = {
        "country": City.country
    }
    _filter_map = {
        "name": City.name,
        "country_id": City.country_id,
        "status": City.status,
        "public_id": City.public_id,
    }

    
    async def create(
        self,
        city: City,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> City:
        self.db.add(city)
        if commit:
            await self.db.commit()
            await self.db.refresh(city)
        if with_relations:
            query = self._apply_relations(
                select(City).where(City.id == city.id),
                with_relations,
                self._relation_map,
            )
            return await self._fetch_one(query)
        return city

    
    async def get_by_name(
        self,
        name: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
   ) -> Optional[City]:
        query = self._apply_relations(
            select(City).where(City.name.ilike(name.strip())),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_id(
        self,
        city_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[City]:
        query = self._apply_relations(
            select(City).where(City.id == city_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)
    
    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[City]:
        query = self._apply_relations(
            select(City).where(City.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)


    
    async def list(
            self,
            page: int = 1,
            page_size: int = 20,
            search: Optional[str] = None,
            filters: Optional[list[dict[str, str]]] = None,
            with_relations: Optional[WithRelations] = None,
            flush: bool = False,
        ) -> Page[City]:
            query = select(City).order_by(City.created_at.desc())
            query = self._apply_search(query, search, search_fields=[City.name, City.country_id])
            query = self._apply_dynamic_filters(query, filters, self._filter_map)
            query = self._apply_relations(query, with_relations, self._relation_map)
    
            return await self._paginate(query, page=page, page_size=page_size, flush=flush)
