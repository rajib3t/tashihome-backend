from app.repositories.location_repository import LocationRepository, WithRelations
from app.models.location_model import Location

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