from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.room_block_model import RoomBlock
from app.services.room_block_service import RoomBlockService

_RELATIONS = {
    "property": True,
    "room_type": True,
    "creator": True,
}


class VendorDeleteRoomBlockUseCase(BaseUseCase):
    def __init__(self, room_block_service: RoomBlockService, current_user: CurrentUser):
        self.room_block_service = room_block_service
        self.current_user = current_user

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

        if room_block.property and room_block.property.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You do not have access to this room block.",
                error_code="ROOM_BLOCK_ACCESS_DENIED",
            )

        await self.room_block_service.delete(room_block=room_block, commit=True)
        return room_block

