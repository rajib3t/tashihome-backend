from fastapi.params import Depends

from app.application.use_case.attributes.attribute.create_room_type_use_case import CreateRoomTypeUseCase
from app.application.use_case.attributes.attribute.get_room_type_use_case import ListRoomTypesUseCase
from app.application.use_case.attributes.attribute.update_room_type_use_case import (
    UpdateRoomTypeUseCase,
    UpdateStatusRoomTypeUseCase,
)
from app.core.csrf import verify_csrf
from app.deps.auth import CurrentUser, require_admin
from app.deps.service import get_room_type_service
from app.services.room_type_service import RoomTypeService


async def get_create_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin),
):
    return CreateRoomTypeUseCase(room_type_service, verify_csrf, current_user)


async def get_list_room_types_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_admin),
):
    return ListRoomTypesUseCase(room_type_service, current_user)


async def get_update_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_admin),
):
    return UpdateRoomTypeUseCase(room_type_service, current_user)


async def get_update_status_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_admin),
):
    return UpdateStatusRoomTypeUseCase(room_type_service, current_user)
