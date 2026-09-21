from __future__ import annotations
from typing import Optional

from app.models.room_type_model import RoomType
from app.repositories.base_repository import Page


class RoomTypeService:
    def __init__(self, room_type_repository):
        self.room_type_repository = room_type_repository

    async def create(
        self,
        room_type: RoomType,
        commit: bool = True,
    ) -> RoomType:
        return await self.room_type_repository.create(room_type, commit=commit)

    async def get_by_name(
        self,
        name: str,
        flush: bool = False,
    ) -> Optional[RoomType]:
        return await self.room_type_repository.get_by_name(name, flush=flush)

    async def get_by_name_and_vendor(
        self,
        name: str,
        vendor_id: Optional[int] = None,
        flush: bool = False,
    ) -> Optional[RoomType]:
        return await self.room_type_repository.get_by_name_and_vendor(name, vendor_id=vendor_id, flush=flush)

    async def get_by_id(
        self,
        room_type_id: int,
        flush: bool = False,
    ) -> Optional[RoomType]:
        return await self.room_type_repository.get_by_id(room_type_id, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        flush: bool = False,
    ) -> Optional[RoomType]:
        return await self.room_type_repository.get_by_public_id(public_id, flush=flush)

    async def update(
        self,
        room_type: RoomType,
        commit: bool = True,
    ) -> RoomType:
        return await self.room_type_repository.update(room_type, commit=commit)

    async def delete(
        self,
        room_type: RoomType,
        commit: bool = True,
    ) -> None:
        await self.room_type_repository.delete(room_type, commit=commit)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        vendor_id: Optional[int] = None,
        scope: str = "all",
        flush: bool = False,
    ) -> Page[RoomType]:
        return await self.room_type_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            vendor_id=vendor_id,
            scope=scope,
            flush=flush,
        )

    async def get_by_public_ids(
        self,
        public_ids: list[str],
        flush: bool = False,
    ) -> list[RoomType]:
        return await self.room_type_repository.get_by_public_ids(public_ids, flush=flush)

