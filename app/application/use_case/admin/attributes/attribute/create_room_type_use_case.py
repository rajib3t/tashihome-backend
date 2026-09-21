from typing import Optional

from app.application.dto.attributes.room_type import RoomTypeDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.room_type_model import RoomType
from app.services.room_type_service import RoomTypeService
from app.services.user_service import UserService


class CreateRoomTypeUseCase(BaseUseCase):
    def __init__(
        self,
        room_type_service: RoomTypeService,
        verify_csrf: bool,
        current_user: CurrentUser,
        user_service: Optional[UserService] = None,
    ):
        self.room_type_service = room_type_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user
        self.user_service = user_service

    async def execute(self, room_type_dto: RoomTypeDTO) -> RoomType:
        target_vendor_id = None
        target_vendor = None
        if room_type_dto.vendor_id and str(room_type_dto.vendor_id).strip():
            raw_vid = str(room_type_dto.vendor_id).strip()
            if self.user_service:
                target_vendor = await self.user_service.get_user_by_public_id(raw_vid, flush=True)
                if not target_vendor and raw_vid.isdigit():
                    target_vendor = await self.user_service.get_user_by_id(int(raw_vid), flush=True)
                if not target_vendor:
                    raise AppException(
                        status_code=404,
                        message="Vendor not found.",
                        error_code="VENDOR_NOT_FOUND",
                        field="vendor_id",
                    )
                target_vendor_id = target_vendor.id
            elif raw_vid.isdigit():
                target_vendor_id = int(raw_vid)
            else:
                target_vendor_id = raw_vid

        if await self.room_type_service.get_by_name_and_vendor(room_type_dto.name.lower(), vendor_id=None):
            raise AppException(
                status_code=409,
                message="A room type with this name already exists as a global attribute.",
                error_code="ROOM_TYPE_ALREADY_EXISTS_GLOBAL",
                field="name",
            )

        if target_vendor_id is not None and await self.room_type_service.get_by_name_and_vendor(
            room_type_dto.name.lower(), vendor_id=target_vendor_id
        ):
            raise AppException(
                status_code=409,
                message="This vendor already has a room type with this name.",
                error_code="ROOM_TYPE_ALREADY_EXISTS_VENDOR",
                field="name",
            )

        room_type_obj = RoomType(
            name=room_type_dto.name,
            capacity=room_type_dto.capacity,
            vendor_id=target_vendor_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        if target_vendor:
            room_type_obj.vendor = target_vendor

        rt = await self.room_type_service.create(room_type_obj, commit=True)
        if target_vendor:
            rt.vendor = target_vendor
        return rt
