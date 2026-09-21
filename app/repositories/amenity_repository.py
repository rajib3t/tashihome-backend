from __future__ import annotations
from typing import Optional, List

from sqlalchemy import select

from app.models.amenity_model import Amenity
from app.repositories.base_repository import BaseRepository, Page


class AmenityRepository(BaseRepository[Amenity]):
    _filter_map = {
        "name": Amenity.name,
        "status": Amenity.status,
    }

    async def get_by_name(self, name: str, flush: bool = False) -> Amenity | None:
        query = select(Amenity).where(Amenity.name.ilike(name.strip()))
        return await self._fetch_one(query, flush=flush)

    async def get_by_id(self, amenity_id: int, flush: bool = False) -> Amenity | None:
        query = select(Amenity).where(Amenity.id == amenity_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Amenity | None:
        query = select(Amenity).where(Amenity.public_id == public_id)
        return await self._fetch_one(query, flush=flush)

    async def create(self, amenity: Amenity, commit: bool = True) -> Amenity:
        self.db.add(amenity)
        if commit:
            await self.db.commit()
            await self.db.refresh(amenity)
        return amenity

    async def update(self, amenity: Amenity, commit: bool = True) -> Amenity:
        self.db.add(amenity)
        if commit:
            await self.db.commit()
            await self.db.refresh(amenity)
        return amenity

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        flush: bool = False,
    ) -> Page[Amenity]:
        query = select(Amenity).order_by(Amenity.created_at.desc())
        query = self._apply_search(query, search, search_fields=[Amenity.name])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def get_all(self) -> list[Amenity]:
        query = select(Amenity)
        return await self._fetch_all(query)

    async def get_by_public_ids(self, public_ids: list[str], flush: bool = False) -> list[Amenity]:
        if not public_ids:
            return []
        import uuid
        parsed_ids = []
        for pid in public_ids:
            if isinstance(pid, uuid.UUID):
                parsed_ids.append(pid)
            elif isinstance(pid, str) and pid.strip():
                try:
                    parsed_ids.append(uuid.UUID(pid.strip()))
                except ValueError:
                    pass
        if not parsed_ids:
            return []
        query = select(Amenity).where(Amenity.public_id.in_(parsed_ids))
        return await self._fetch_all(query, flush=flush)


