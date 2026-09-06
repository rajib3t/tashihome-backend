from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.property_room_type_price_model import PropertyRoomTypePrice
from app.repositories.base_repository import BaseRepository


class WithRelations(TypedDict, total=False):
    property_room_type: bool


class PropertyRoomTypePriceRepository(BaseRepository[PropertyRoomTypePrice]):
    _relation_map = {
        "property_room_type": PropertyRoomTypePrice.property_room_type,
    }
    _filter_map = {
        "property_room_type_id": PropertyRoomTypePrice.property_room_type_id,
        "occupancy": PropertyRoomTypePrice.occupancy,
        "public_id": PropertyRoomTypePrice.public_id,
    }

    async def create(
        self,
        price_tier: PropertyRoomTypePrice,
        commit: bool = True,
    ) -> PropertyRoomTypePrice:
        self.db.add(price_tier)
        if commit:
            await self.db.commit()
            await self.db.refresh(price_tier)
        return price_tier

    async def get_by_id(
        self,
        price_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyRoomTypePrice]:
        query = self._apply_relations(
            select(PropertyRoomTypePrice).where(PropertyRoomTypePrice.id == price_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyRoomTypePrice]:
        query = self._apply_relations(
            select(PropertyRoomTypePrice).where(PropertyRoomTypePrice.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_property_room_type_id(
        self,
        property_room_type_id: int,
        flush: bool = False,
    ) -> list[PropertyRoomTypePrice]:
        query = (
            select(PropertyRoomTypePrice)
            .where(PropertyRoomTypePrice.property_room_type_id == property_room_type_id)
            .order_by(PropertyRoomTypePrice.occupancy.asc())
        )
        return await self._fetch_all(query, flush=flush)

    async def get_by_occupancy(
        self,
        property_room_type_id: int,
        occupancy: int,
        flush: bool = False,
    ) -> Optional[PropertyRoomTypePrice]:
        query = select(PropertyRoomTypePrice).where(
            PropertyRoomTypePrice.property_room_type_id == property_room_type_id,
            PropertyRoomTypePrice.occupancy == occupancy,
        )
        return await self._fetch_one(query, flush=flush)

