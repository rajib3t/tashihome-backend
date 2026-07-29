from typing import Optional, TypedDict

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.city_model import City
from app.models.location_model import Location
from app.repositories.base_repository import BaseRepository

class WithRelations(TypedDict, total=False):
    city: bool

class LocationRepository(BaseRepository[Location]):
    _relation_map = {
        "city": Location.city
    }
    _filter_map = {
        "name": Location.name,
        "status": Location.status,
        "city_id": Location.city_id,
        "public_id": Location.public_id,
    }


    async def create(
        self,
        location: Location,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Location:
            
        self.db.add(location)
        if commit:
            await self.db.commit()
            await self.db.refresh(location)
        return location

    async def get_by_name_and_city_id(
        self,
        name: str,
        city_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Location]:
        query = self._apply_relations(
            select(Location).where(
                Location.city_id == city_id,
                Location.name.ilike(name.strip()),
            ),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_id_with_city_country(
        self,
        location_id: int,
        flush: bool = False,
    ) -> Optional[Location]:
        query = (
            select(Location)
            .where(Location.id == location_id)
            .options(
                selectinload(Location.city).selectinload(City.country)
            )
        )
        return await self._fetch_one(query, flush=flush)
