from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.services.room_type_service import RoomTypeService


class VendorDeleteRoomTypeUseCase(BaseUseCase):
    def __init__(
        self,
        room_type_service: RoomTypeService,
        current_user: CurrentUser,
    ):
        self.room_type_service = room_type_service
        self.current_user = current_user

    async def execute(self, room_type_id: str) -> None:
        existing_room_type = await self.room_type_service.get_by_public_id(
            public_id=room_type_id, flush=False
        )
        if not existing_room_type:
            raise AppException(
                status_code=404,
                message="Room type not found",
                error_code="ROOM_TYPE_NOT_FOUND",
                field="room_type_id",
            )

        if existing_room_type.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You do not have permission to delete this room type.",
                error_code="ROOM_TYPE_FORBIDDEN",
                field="room_type_id",
            )

        await self.room_type_service.delete(existing_room_type, commit=True)

