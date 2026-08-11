
from app.repositories.property_room_type_repository import PropertyRoomTypeRepository
from app.models.property_room_type_model import PropertyRoomType
from app.repositories.base_repository import WithRelations
from typing import Optional

class PropertyRoomTypeService:
    def __init__(self, property_room_type_repository: PropertyRoomTypeRepository):
        self.property_room_type_repository = property_room_type_repository


    
    async def create(
        self,
        property_room_type: PropertyRoomType,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyRoomType:
        return await self.property_room_type_repository.create(property_room_type, with_relations=with_relations, commit=commit)

    async def get_by_id(
        self,
        property_room_type_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyRoomType]:
        return await self.property_room_type_repository.get_by_id(property_room_type_id, with_relations=with_relations, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[PropertyRoomType]:
        return await self.property_room_type_repository.get_by_public_id(public_id, with_relations=with_relations, flush=flush)

    async def get_by_property_id(
        self,
        property_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> list[PropertyRoomType]:
        return await self.property_room_type_repository.get_by_property_id(property_id, with_relations=with_relations, flush=flush)

    async def update(
        self,
        property_room_type: PropertyRoomType,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> PropertyRoomType:
        return await self.property_room_type_repository.update(property_room_type, with_relations=with_relations, commit=commit)

    async def delete(
        self,
        property_room_type: PropertyRoomType,
        commit: bool = True,
    ) -> None:
        await self.property_room_type_repository.delete(property_room_type, commit=commit)
    