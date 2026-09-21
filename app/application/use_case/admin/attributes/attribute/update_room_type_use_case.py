from typing import Optional
from app.application.dto.attributes.room_type import RoomTypeDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.room_type_model import RoomType, RoomTypeStatus
from app.services.room_type_service import RoomTypeService
from app.services.user_service import UserService


class UpdateRoomTypeUseCase(BaseUseCase):
    def __init__(
        self,
        room_type_service: RoomTypeService,
        current_user: CurrentUser,
        user_service: Optional[UserService] = None,
    ):
        self.room_type_service = room_type_service
        self.current_user = current_user
        self.user_service = user_service

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

        target_vendor_id = existing_room_type.vendor_id
        target_vendor = getattr(existing_room_type, "vendor", None)
        if room_type_dto.vendor_id is not None:
            raw_vid = str(room_type_dto.vendor_id).strip()
            if not raw_vid:
                target_vendor_id = None
                target_vendor = None
            elif self.user_service:
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

        duplicate_name = await self.room_type_service.get_by_name_and_vendor(
            name=room_type_dto.name.lower(),
            vendor_id=target_vendor_id,
        )
        if duplicate_name and duplicate_name.id != existing_room_type.id:
            raise AppException(
                status_code=409,
                message="A room type with this name already exists.",
                error_code="ROOM_TYPE_ALREADY_EXISTS",
                field="name",
            )

        existing_room_type.name = room_type_dto.name
        existing_room_type.capacity = room_type_dto.capacity
        existing_room_type.vendor_id = target_vendor_id
        if target_vendor is not None or target_vendor_id is None:
            existing_room_type.vendor = target_vendor
        existing_room_type.updated_by = self.current_user.id

        rt = await self.room_type_service.update(existing_room_type, commit=True)
        if target_vendor:
            rt.vendor = target_vendor
        return rt


class UpdateStatusRoomTypeUseCase(BaseUseCase):
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
