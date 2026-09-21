from app.application.dto.attributes.room_type import RoomTypeDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.room_type_model import RoomType
from app.services.room_type_service import RoomTypeService


class VendorCreateRoomTypeUseCase(BaseUseCase):
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
        normalized_name = room_type_dto.name.strip()

        # 1. Vendor cannot create with same name as global
        if await self.room_type_service.get_by_name_and_vendor(normalized_name.lower(), vendor_id=None):
            raise AppException(
                status_code=409,
                message="A room type with this name already exists as a global attribute.",
                error_code="ROOM_TYPE_ALREADY_EXISTS_GLOBAL",
                field="name",
            )

        # 2. Vendor cannot create duplicate within own room types
        if await self.room_type_service.get_by_name_and_vendor(normalized_name.lower(), vendor_id=self.current_user.id):
            raise AppException(
                status_code=409,
                message="You already have a room type with this name.",
                error_code="ROOM_TYPE_ALREADY_EXISTS_VENDOR",
                field="name",
            )

        room_type_obj = RoomType(
            name=normalized_name,
            capacity=room_type_dto.capacity,
            vendor_id=self.current_user.id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        return await self.room_type_service.create(room_type_obj, commit=True)

