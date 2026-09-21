from __future__ import annotations
from typing import Optional, List

from sqlalchemy import select

from app.models.room_type_model import RoomType
from app.repositories.base_repository import BaseRepository, Page


class RoomTypeRepository(BaseRepository[RoomType]):
    _filter_map = {
        "name": RoomType.name,
        "status": RoomType.status,
    }

    async def get_by_name(self, name: str, flush: bool = False) -> RoomType | None:
        query = select(RoomType).where(RoomType.name.ilike(name.strip()))
        return await self._fetch_one(query, flush=flush)

    async def get_by_id(self, room_type_id: int, flush: bool = False) -> RoomType | None:
        query = select(RoomType).where(RoomType.id == room_type_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> RoomType | None:
        query = select(RoomType).where(RoomType.public_id == public_id)
        return await self._fetch_one(query, flush=flush)

    async def create(self, room_type: RoomType, commit: bool = True) -> RoomType:
        self.db.add(room_type)
        if commit:
            await self.db.commit()
            await self.db.refresh(room_type)
        return room_type

    async def update(self, room_type: RoomType, commit: bool = True) -> RoomType:
        self.db.add(room_type)
        if commit:
            await self.db.commit()
            await self.db.refresh(room_type)
        return room_type

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        flush: bool = False,
    ) -> Page[RoomType]:
        query = select(RoomType).order_by(RoomType.created_at.desc())
        query = self._apply_search(query, search, search_fields=[RoomType.name])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def get_all(self) -> list[RoomType]:
        query = select(RoomType)
        return await self._fetch_all(query)

    async def get_by_public_ids(self, public_ids: list[str], flush: bool = False) -> list[RoomType]:
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
        query = select(RoomType).where(RoomType.public_id.in_(parsed_ids))
        return await self._fetch_all(query, flush=flush)


