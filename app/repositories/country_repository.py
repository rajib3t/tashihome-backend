from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.country_model import Country
from app.repositories.base_repository import BaseRepository, Page

class WithRelations(TypedDict, total=False):
    cities: bool
class CountryRepository(BaseRepository[Country]):
    
    _relation_map = {
        "cities": Country.cities
    }
    _filter_map = {
        "name": Country.name,
        "code": Country.code,
        "status": Country.status,
        "public_id": Country.public_id,
    }
     
    
    async def create(
        self,
        country: Country,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Country:
    
        self.db.add(country)
        if commit:
            await self.db.commit()
            await self.db.refresh(country)
        return country
    
    async def get_by_id(
        self,
        country_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Country]:
        query = self._apply_relations(
            select(Country).where(Country.id == country_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)
    
    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Country]:
        query = self._apply_relations(
            select(Country).where(Country.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)
    

    async def get_by_name(
        self,
        name: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Country]:
        query = self._apply_relations(
            select(Country).where(Country.name.ilike(name.strip())),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)
    
    async def get_by_code(
        self,
        code: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Country]:
        query = self._apply_relations(
            select(Country).where(Country.code.upper() == code.upper()),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)
    
    async def update(
        self,
        country: Country,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Country:
        if not commit:
            return country

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(Country).where(Country.id == country.id),
                with_relations,
                self._relation_map,
            )
            # Data was just committed, so no flush is needed here.
            await self.db.commit()
            return await self._fetch_one(query)
        
        await self.db.commit()
        await self.db.refresh(country)
        return country
    
    async def status_update(
        self,
        country: Country,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Country:
        if not commit:
            return country

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(Country).where(Country.id == country.id),
                with_relations,
                self._relation_map,
            )
            # Data was just committed, so no flush is needed here.
            await self.db.commit()
            return await self._fetch_one(query)
        
        await self.db.commit()
        await self.db.refresh(country)
        return country
    
    async def delete(
        self,
        country: Country,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> None:
        await self.db.delete(country)
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
    ) -> Page[Country]:
        query = select(Country).order_by(Country.created_at.desc())
        query = self._apply_search(query, search, search_fields=[Country.name, Country.code])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        query = self._apply_relations(query, with_relations, self._relation_map)

        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    
