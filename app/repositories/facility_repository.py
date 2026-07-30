from select import select
from typing import Optional

from PIL.ImageChops import offset

from app.models.facility_model import Facility
from app.repositories.base_repository import BaseRepository, Page


class FacilityRepository(BaseRepository[Facility]):

    _filter_map = {
        "name": Facility.name,
       "status": Facility.status,
    }

    async def get_by_name(self, name: str, flush: bool = False) -> Facility | None:
        query = select(Facility).where(Facility.name.ilike(name.strip()))
        return await self._fetch_one(query, flush=flush)

    async def get_by_id(self, facility_id: int, flush: bool = False) -> Facility | None:
        query = select(Facility).where(Facility.id == facility_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Facility | None:
        query = select(Facility).where(Facility.public_id == public_id)
        return await self._fetch_one(query, flush=flush)

    async def create(self, facility: Facility, commit: bool = True) -> Facility:
        self.db.add(facility)
        if commit:
            await self.db.commit()
            await self.db.refresh(facility)
        return facility

    async def update(self, facility: Facility, commit: bool = True) -> Facility:
        self.db.add(facility)
        if commit:
            await self.db.commit()
            await self.db.refresh(facility)
        return facility

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        flush: bool = False,
    ) -> Page[Facility]:
        query = select(Facility).order_by(Facility.created_at.desc())
        query = self._apply_search(query, search, search_fields=[Facility.name])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)
    