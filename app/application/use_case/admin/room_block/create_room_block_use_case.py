from datetime import date
from typing import Optional
from uuid import UUID

from app.application.dto.room_blocks.room_block import RoomBlockCreateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.room_block_model import RoomBlock
from app.services.property_room_type_service import PropertyRoomTypeService
from app.services.property_service import PropertyService
from app.services.room_block_service import RoomBlockService
from app.services.room_type_service import RoomTypeService

_RELATIONS = {
    "property": True,
    "room_type": True,
    "creator": True,
}


class AdminCreateRoomBlockUseCase(BaseUseCase):
    def __init__(
        self,
        room_block_service: RoomBlockService,
        property_service: PropertyService,
        room_type_service: RoomTypeService,
        property_room_type_service: PropertyRoomTypeService,
        current_user: CurrentUser,
    ):
        self.room_block_service = room_block_service
        self.property_service = property_service
        self.room_type_service = room_type_service
        self.property_room_type_service = property_room_type_service
        self.current_user = current_user

    async def execute(self, data: RoomBlockCreateDTO) -> RoomBlock:
        today = date.today()
        if data.block_start_date < today:
            raise AppException(
                status_code=400,
                message="Block start date cannot be in the past.",
                error_code="INVALID_START_DATE",
                field="block_start_date",
            )

        if data.block_end_date <= data.block_start_date:
            raise AppException(
                status_code=400,
                message="Block end date must be after block start date.",
                error_code="INVALID_END_DATE",
                field="block_end_date",
            )

        # 1. Resolve Property
        property_ = None
        try:
            uuid_obj = UUID(str(data.property_id))
            property_ = await self.property_service.get_by_public_id(str(uuid_obj))
        except (ValueError, AttributeError):
            if str(data.property_id).isdigit():
                property_ = await self.property_service.get_by_id(int(data.property_id))
            else:
                property_ = await self.property_service.get_by_slug(str(data.property_id))

        if not property_:
            raise AppException(
                status_code=404,
                message="Property not found.",
                error_code="PROPERTY_NOT_FOUND",
                field="property_id",
            )

        # 2. Resolve Room Type
        room_type = None
        try:
            rt_uuid = UUID(str(data.room_type_id))
            room_type = await self.room_type_service.get_by_public_id(str(rt_uuid))
            if not room_type:
                prop_rt = await self.property_room_type_service.get_by_public_id(str(rt_uuid))
                if prop_rt:
                    room_type = await self.room_type_service.get_by_id(prop_rt.room_type_id)
        except (ValueError, AttributeError):
            if str(data.room_type_id).isdigit():
                room_type = await self.room_type_service.get_by_id(int(data.room_type_id))
                if not room_type:
                    prop_rt = await self.property_room_type_service.get_by_id(int(data.room_type_id))
                    if prop_rt:
                        room_type = await self.room_type_service.get_by_id(prop_rt.room_type_id)

        if not room_type:
            raise AppException(
                status_code=404,
                message="Room type not found.",
                error_code="ROOM_TYPE_NOT_FOUND",
                field="room_type_id",
            )

        # 3. Verify Room Type belongs to Property
        prop_room_type = await self.property_room_type_service.get_by_property_and_room_type(
            property_.id, room_type.id
        )
        if not prop_room_type:
            raise AppException(
                status_code=400,
                message="The specified room type is not configured on this property.",
                error_code="ROOM_TYPE_NOT_ON_PROPERTY",
                field="room_type_id",
            )

        # 4. Check capacity and existing bookings
        await self.room_block_service.validate_and_check_capacity(
            property_id=property_.id,
            room_type_id=room_type.id,
            block_start_date=data.block_start_date,
            block_end_date=data.block_end_date,
            units_to_block=data.units_blocked,
        )

        # 5. Create Room Block
        room_block = RoomBlock(
            property_id=property_.id,
            room_type_id=room_type.id,
            block_start_date=data.block_start_date,
            block_end_date=data.block_end_date,
            units_blocked=data.units_blocked,
            reason=data.reason,
            created_by=self.current_user.id,
        )

        return await self.room_block_service.create(
            room_block=room_block,
            with_relations=_RELATIONS,
        )

