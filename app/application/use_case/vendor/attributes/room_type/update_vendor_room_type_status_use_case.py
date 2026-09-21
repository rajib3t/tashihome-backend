from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.room_type_model import RoomType, RoomTypeStatus
from app.services.room_type_service import RoomTypeService


class VendorUpdateRoomTypeStatusUseCase(BaseUseCase):
    def __init__(
        self,
        room_type_service: RoomTypeService,
        current_user: CurrentUser,
    ):
        self.room_type_service = room_type_service
        self.current_user = current_user

    async def execute(self, room_type_id: str, status: str) -> RoomType:
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
                message="You do not have permission to update this room type status.",
                error_code="ROOM_TYPE_FORBIDDEN",
                field="room_type_id",
            )

        normalized_status = status.strip().lower()
        if normalized_status not in ["active", "inactive"]:
            raise AppException(
                status_code=422,
                message="Status must be either 'active' or 'inactive'.",
                field="status",
                error_code="STATUS_INVALID",
            )

        existing_room_type.status = (
            RoomTypeStatus.ACTIVE if normalized_status == "active" else RoomTypeStatus.INACTIVE
        )
        existing_room_type.updated_by = self.current_user.id

        return await self.room_type_service.update(existing_room_type, commit=True)

