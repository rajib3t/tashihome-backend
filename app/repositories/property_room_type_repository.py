from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.property_room_type_model import PropertyRoomType
from app.repositories.base_repository import BaseRepository

class WithRelations(TypedDict, total=False):
    property: bool
    room_type: bool
    property_room_units: bool
    pricing_tiers: bool

class PropertyRoomTypeRepository(BaseRepository[PropertyRoomType]):
    
    _relation_map = {
        "property": PropertyRoomType.property,
        "room_type": PropertyRoomType.room_type,
        "property_room_units": PropertyRoomType.property_room_units,
        "pricing_tiers": PropertyRoomType.pricing_tiers,
    }
    _filter_map = {
        "property_id": PropertyRoomType.property_id,
        "room_type_id": PropertyRoomType.room_type_id,
        "public_id": PropertyRoomType.public_id,
    }

    

    async def create(
        self,
        property_room_type: PropertyRoomType,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyRoomType:
        self.db.add(property_room_type)
        if with_relations:
            query = self._apply_relations(
                select(PropertyRoomType).where(PropertyRoomType.id == property_room_type.id),
                with_relations,
                self._relation_map,
            )
            property_room_type = await self._fetch_one(query)
        if commit:
            await self.db.commit()
            await self.db.refresh(property_room_type)
        return property_room_type


    
    async def get_by_id(
        self,
        property_room_type_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyRoomType]:
        query = self._apply_relations(
            select(PropertyRoomType).where(PropertyRoomType.id == property_room_type_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyRoomType]:
        query = self._apply_relations(
            select(PropertyRoomType).where(PropertyRoomType.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyRoomType]:
        query = self._apply_relations(
            select(PropertyRoomType).where(PropertyRoomType.property_id == property_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_all(query, flush=flush)

    async def get_by_property_and_room_type(
        self,
        property_id: int,
        room_type_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyRoomType]:
        query = self._apply_relations(
            select(PropertyRoomType).where(
                PropertyRoomType.property_id == property_id,
                PropertyRoomType.room_type_id == room_type_id,
            ),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def update(
        self,
        property_room_type: PropertyRoomType,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyRoomType:
        if not commit:
            return property_room_type

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(PropertyRoomType).where(PropertyRoomType.id == property_room_type.id),
                with_relations,
                self._relation_map,
            )
            return await self._fetch_one(query)

        await self.db.refresh(property_room_type)
        return property_room_type

    async def delete(
        self,
        property_room_type: PropertyRoomType,
        commit: bool = True,
    ) -> None:
        await self.db.delete(property_room_type)
        if commit:
            await self.db.commit()
