from datetime import date
from typing import Optional

from app.application.dto.room_blocks.room_block import RoomBlockUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.room_block_model import RoomBlock
from app.services.room_block_service import RoomBlockService

_RELATIONS = {
    "property": True,
    "room_type": True,
    "creator": True,
}


class AdminUpdateRoomBlockUseCase(BaseUseCase):
    def __init__(self, room_block_service: RoomBlockService):
        self.room_block_service = room_block_service

    async def execute(self, block_identifier: str, data: RoomBlockUpdateDTO) -> RoomBlock:
        room_block = await self.room_block_service.get_by_identifier(
            identifier=block_identifier,
            with_relations=_RELATIONS,
        )
        if not room_block:
            raise AppException(
                status_code=404,
                message="Room block not found.",
                error_code="ROOM_BLOCK_NOT_FOUND",
                field="room_block_id",
            )

        new_start = data.block_start_date if data.block_start_date is not None else room_block.block_start_date
        new_end = data.block_end_date if data.block_end_date is not None else room_block.block_end_date
        new_units = data.units_blocked if data.units_blocked is not None else room_block.units_blocked

        if new_end <= new_start:
            raise AppException(
                status_code=400,
                message="Block end date must be after block start date.",
                error_code="INVALID_DATES",
                field="block_end_date",
            )

        if (
            new_start != room_block.block_start_date
            or new_end != room_block.block_end_date
            or new_units != room_block.units_blocked
        ):
            await self.room_block_service.validate_and_check_capacity(
                property_id=room_block.property_id,
                room_type_id=room_block.room_type_id,
                block_start_date=new_start,
                block_end_date=new_end,
                units_to_block=new_units,
                exclude_block_id=room_block.id,
            )

        room_block.block_start_date = new_start
        room_block.block_end_date = new_end
        room_block.units_blocked = new_units
        if data.reason is not None:
            room_block.reason = data.reason

        return await self.room_block_service.update(
            room_block=room_block,
            with_relations=_RELATIONS,
            commit=True,
        )

