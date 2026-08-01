from app.application.dto.attributes.room_type import RoomTypeDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.room_type_model import RoomType
from app.services.room_type_service import RoomTypeService


class CreateRoomTypeUseCase(BaseUseCase):
    def __init__(
        self,
        room_type_service: RoomTypeService,
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.room_type_service = room_type_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(self, room_type_dto: RoomTypeDTO) -> RoomType:
        if await self.room_type_service.get_by_name(room_type_dto.name.lower()):
            raise AppException(
                status_code=409,
                message="Room type already exists",
                error_code="ROOM_TYPE_ALREADY_EXISTS",
                field="name",
            )

        room_type_obj = RoomType(
            name=room_type_dto.name,
            capacity=room_type_dto.capacity,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        return await self.room_type_service.create(room_type_obj, commit=True)
