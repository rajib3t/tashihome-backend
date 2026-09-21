from __future__ import annotations
from typing import Optional

from app.models.amenity_model import Amenity
from app.repositories.base_repository import Page


class AmenityService:
    def __init__(self, amenity_repository):
        self.amenity_repository = amenity_repository

    async def create(
        self,
        amenity: Amenity,
        commit: bool = True,
    ) -> Amenity:
        return await self.amenity_repository.create(amenity, commit=commit)

    async def get_by_name(
        self,
        name: str,
        flush: bool = False,
    ) -> Optional[Amenity]:
        return await self.amenity_repository.get_by_name(name, flush=flush)

    async def get_by_name_and_vendor(
        self,
        name: str,
        vendor_id: Optional[int] = None,
        flush: bool = False,
    ) -> Optional[Amenity]:
        return await self.amenity_repository.get_by_name_and_vendor(name, vendor_id=vendor_id, flush=flush)

    async def get_by_id(
        self,
        amenity_id: int,
        flush: bool = False,
    ) -> Optional[Amenity]:
        return await self.amenity_repository.get_by_id(amenity_id, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        flush: bool = False,
    ) -> Optional[Amenity]:
        return await self.amenity_repository.get_by_public_id(public_id, flush=flush)

    async def update(
        self,
        amenity: Amenity,
        commit: bool = True,
    ) -> Amenity:
        return await self.amenity_repository.update(amenity, commit=commit)

    async def delete(
        self,
        amenity: Amenity,
        commit: bool = True,
    ) -> None:
        await self.amenity_repository.delete(amenity, commit=commit)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        vendor_id: Optional[int] = None,
        scope: str = "all",
        flush: bool = False,
    ) -> Page[Amenity]:
        return await self.amenity_repository.list(
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
    ) -> list[Amenity]:
        return await self.amenity_repository.get_by_public_ids(public_ids, flush=flush)

