from typing import Optional
from uuid import UUID

from app.application.dto.room_blocks.room_block import RoomBlockQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.models.room_block_model import RoomBlock
from app.repositories.base_repository import Page
from app.services.property_service import PropertyService
from app.services.room_block_service import RoomBlockService
from app.services.room_type_service import RoomTypeService

_RELATIONS = {
    "property": True,
    "room_type": True,
    "creator": True,
}


class VendorGetRoomBlocksUseCase(BaseUseCase):
    def __init__(
        self,
        room_block_service: RoomBlockService,
        property_service: PropertyService,
        room_type_service: RoomTypeService,
        current_user: CurrentUser,
    ):
        self.room_block_service = room_block_service
        self.property_service = property_service
        self.room_type_service = room_type_service
        self.current_user = current_user

    async def execute(self, params: RoomBlockQueryDTO) -> Page[RoomBlock]:
        property_id_db: Optional[int] = None
        if params.property_id:
            try:
                uuid_obj = UUID(str(params.property_id))
                prop = await self.property_service.get_by_public_id(str(uuid_obj))
            except (ValueError, AttributeError):
                if str(params.property_id).isdigit():
                    prop = await self.property_service.get_by_id(int(params.property_id))
                else:
                    prop = await self.property_service.get_by_slug(str(params.property_id))
            if prop:
                property_id_db = prop.id

        room_type_id_db: Optional[int] = None
        if params.room_type_id:
            try:
                rt_uuid = UUID(str(params.room_type_id))
                rt = await self.room_type_service.get_by_public_id(str(rt_uuid))
            except (ValueError, AttributeError):
                if str(params.room_type_id).isdigit():
                    rt = await self.room_type_service.get_by_id(int(params.room_type_id))
                else:
                    rt = None
            if rt:
                room_type_id_db = rt.id

        return await self.room_block_service.list_vendor_room_blocks(
            vendor_id=self.current_user.id,
            page=params.page,
            page_size=params.size,
            property_id=property_id_db,
            room_type_id=room_type_id_db,
            start_date=params.start_date,
            end_date=params.end_date,
            search=params.search,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            with_relations=_RELATIONS,
        )

