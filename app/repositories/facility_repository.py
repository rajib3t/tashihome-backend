from __future__ import annotations
from typing import Optional, List

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.models.facility_model import Facility
from app.repositories.base_repository import BaseRepository, Page


class FacilityRepository(BaseRepository[Facility]):

    _filter_map = {
        "name": Facility.name,
        "status": Facility.status,
        "vendor_id": Facility.vendor_id,
    }

    async def get_by_name(self, name: str, flush: bool = False) -> Facility | None:
        query = select(Facility).options(selectinload(Facility.vendor)).where(Facility.name.ilike(name.strip()))
        return await self._fetch_one(query, flush=flush)

    async def get_by_name_and_vendor(self, name: str, vendor_id=None, flush: bool = False) -> Facility | None:
        query = select(Facility).options(selectinload(Facility.vendor)).where(
            Facility.name.ilike(name.strip()),
            Facility.vendor_id == vendor_id  # None or specific int
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_id(self, facility_id: int, flush: bool = False) -> Facility | None:
        query = select(Facility).options(selectinload(Facility.vendor)).where(Facility.id == facility_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Facility | None:
        query = select(Facility).options(selectinload(Facility.vendor)).where(Facility.public_id == public_id)
        return await self._fetch_one(query, flush=flush)

    async def create(self, facility: Facility, commit: bool = True) -> Facility:
        self.db.add(facility)
        if commit:
            await self.db.commit()
            fresh = await self.get_by_id(facility.id)
            if fresh:
                return fresh
            await self.db.refresh(facility)
        return facility

    async def update(self, facility: Facility, commit: bool = True) -> Facility:
        self.db.add(facility)
        if commit:
            await self.db.commit()
            fresh = await self.get_by_id(facility.id)
            if fresh:
                return fresh
            await self.db.refresh(facility)
        return facility

    async def delete(self, facility: Facility, commit: bool = True) -> None:
        await self.db.delete(facility)
        if commit:
            await self.db.commit()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        vendor_id: Optional[int] = None,
        scope: str = "all",
        flush: bool = False,
    ) -> Page[Facility]:
        query = select(Facility).options(selectinload(Facility.vendor)).order_by(Facility.created_at.desc())
        query = self._apply_search(query, search, search_fields=[Facility.name])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)

        if scope == "global":
            query = query.where(Facility.vendor_id.is_(None))
        elif scope == "vendor":
            query = query.where(Facility.vendor_id == vendor_id)
        elif scope == "vendor_combined":
            query = query.where(or_(Facility.vendor_id.is_(None), Facility.vendor_id == vendor_id))
        # scope == "all" → no filter

        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def get_all(self) -> list[Facility]:
        query = select(Facility)
        return await self._fetch_all(query)

    async def get_by_public_ids(self, public_ids: list[str], flush: bool = False) -> list[Facility]:
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
        query = select(Facility).where(Facility.public_id.in_(parsed_ids))
        return await self._fetch_all(query, flush=flush)
