from typing import Optional, List

from app.models.property_room_type_price_model import PropertyRoomTypePrice
from app.repositories.property_room_type_price_repository import PropertyRoomTypePriceRepository


class PropertyRoomTypePriceService:
    def __init__(self, repository: PropertyRoomTypePriceRepository):
        self.repository = repository

    async def create(
        self,
        price_tier: PropertyRoomTypePrice,
        commit: bool = True,
    ) -> PropertyRoomTypePrice:
        return await self.repository.create(price_tier, commit=commit)

    async def get_by_id(self, price_id: int, flush: bool = False) -> Optional[PropertyRoomTypePrice]:
        return await self.repository.get_by_id(price_id, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Optional[PropertyRoomTypePrice]:
        return await self.repository.get_by_public_id(public_id, flush=flush)

    async def get_by_property_room_type_id(
        self,
        property_room_type_id: int,
        flush: bool = False,
    ) -> List[PropertyRoomTypePrice]:
        return await self.repository.get_by_property_room_type_id(property_room_type_id, flush=flush)

    async def get_by_occupancy(
        self,
        property_room_type_id: int,
        occupancy: int,
        flush: bool = False,
    ) -> Optional[PropertyRoomTypePrice]:
        return await self.repository.get_by_occupancy(property_room_type_id, occupancy, flush=flush)

    async def delete(self, price_tier: PropertyRoomTypePrice, commit: bool = True) -> None:
        await self.repository.delete(price_tier, commit=commit)

