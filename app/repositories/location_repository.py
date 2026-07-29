from typing import Optional, TypedDict

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
