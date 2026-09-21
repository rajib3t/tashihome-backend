from __future__ import annotations
from typing import Optional

from app.models.facility_model import Facility
from app.repositories.base_repository import Page


class FacilityService:
    def __init__(self, facility_repository):
        self.facility_repository = facility_repository


    async def create(
        self,
        facility: Facility,
        commit: bool = True,
    ) -> Facility:
        return await self.facility_repository.create(facility, commit=commit) 

    async def get_by_name(
        self,
        name: str,
        flush: bool = False,
    ) -> Optional[Facility]:
        return await self.facility_repository.get_by_name(name, flush=flush)

    async def get_by_name_and_vendor(
        self,
        name: str,
        vendor_id: Optional[int] = None,
        flush: bool = False,
    ) -> Optional[Facility]:
        return await self.facility_repository.get_by_name_and_vendor(name, vendor_id=vendor_id, flush=flush)

    async def get_by_id(
        self,
        facility_id: int,
        flush: bool = False,
    ) -> Optional[Facility]:
        return await self.facility_repository.get_by_id(facility_id, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        flush: bool = False,
    ) -> Optional[Facility]:
        return await self.facility_repository.get_by_public_id(public_id, flush=flush)

    async def update(
        self,
        facility: Facility,
        commit: bool = True,
    ) -> Facility:
        return await self.facility_repository.update(facility, commit=commit)

    async def delete(
        self,
        facility: Facility,
        commit: bool = True,
    ) -> None:
        await self.facility_repository.delete(facility, commit=commit)

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
        return await self.facility_repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            vendor_id=vendor_id,
            scope=scope,
            flush=flush,
        )

    async def get_all(self) -> list[Facility]:
        return await self.facility_repository.get_all()

    async def get_by_public_ids(
        self,
        public_ids: list[str],
        flush: bool = False,
    ) -> list[Facility]:
        return await self.facility_repository.get_by_public_ids(public_ids, flush=flush)