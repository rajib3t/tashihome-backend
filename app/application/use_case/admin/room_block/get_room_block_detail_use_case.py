from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.room_block_model import RoomBlock
from app.services.room_block_service import RoomBlockService

_RELATIONS = {
    "property": True,
    "room_type": True,
    "creator": True,
}


class AdminGetRoomBlockDetailUseCase(BaseUseCase):
    def __init__(self, room_block_service: RoomBlockService):
        self.room_block_service = room_block_service

    async def execute(self, block_identifier: str) -> RoomBlock:
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
        return room_block

