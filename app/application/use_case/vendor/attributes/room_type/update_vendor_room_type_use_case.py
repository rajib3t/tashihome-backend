from app.application.dto.attributes.room_type import RoomTypeDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.room_type_model import RoomType
from app.services.room_type_service import RoomTypeService


class VendorUpdateRoomTypeUseCase(BaseUseCase):
    def __init__(
        self,
        room_type_service: RoomTypeService,
        current_user: CurrentUser,
    ):
        self.room_type_service = room_type_service
        self.current_user = current_user

    async def execute(self, room_type_id: str, room_type_dto: RoomTypeDTO) -> RoomType:
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
                message="You do not have permission to edit this room type.",
                error_code="ROOM_TYPE_FORBIDDEN",
                field="room_type_id",
            )

        normalized_name = room_type_dto.name.strip()

        # Cannot conflict with global
        if await self.room_type_service.get_by_name_and_vendor(normalized_name.lower(), vendor_id=None):
            raise AppException(
                status_code=409,
                message="A room type with this name already exists as a global attribute.",
                error_code="ROOM_TYPE_ALREADY_EXISTS_GLOBAL",
                field="name",
            )

        # Cannot conflict with another of vendor's room types
        dup = await self.room_type_service.get_by_name_and_vendor(
            normalized_name.lower(), vendor_id=self.current_user.id
        )
        if dup and dup.id != existing_room_type.id:
            raise AppException(
                status_code=409,
                message="You already have a room type with this name.",
                error_code="ROOM_TYPE_ALREADY_EXISTS_VENDOR",
                field="name",
            )

        existing_room_type.name = normalized_name
        existing_room_type.capacity = room_type_dto.capacity
        existing_room_type.updated_by = self.current_user.id

        return await self.room_type_service.update(existing_room_type, commit=True)

