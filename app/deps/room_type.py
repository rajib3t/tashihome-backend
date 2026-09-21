from fastapi.params import Depends

from app.application.use_case.admin.attributes.attribute.create_room_type_use_case import CreateRoomTypeUseCase
from app.application.use_case.admin.attributes.attribute.get_room_type_use_case import ListRoomTypesUseCase
from app.application.use_case.admin.attributes.attribute.update_room_type_use_case import (
    UpdateRoomTypeUseCase,
    UpdateStatusRoomTypeUseCase,
)
from app.application.use_case.vendor.attributes.room_type.create_vendor_room_type_use_case import VendorCreateRoomTypeUseCase
from app.application.use_case.vendor.attributes.room_type.delete_vendor_room_type_use_case import VendorDeleteRoomTypeUseCase
from app.application.use_case.vendor.attributes.room_type.list_vendor_room_types_use_case import VendorListRoomTypesUseCase
from app.application.use_case.vendor.attributes.room_type.update_vendor_room_type_status_use_case import VendorUpdateRoomTypeStatusUseCase
from app.application.use_case.vendor.attributes.room_type.update_vendor_room_type_use_case import VendorUpdateRoomTypeUseCase
from app.core.csrf import verify_csrf
from app.deps.auth import CurrentUser, require_admin, require_admin_or_staff, require_vendor
from app.deps.service import get_room_type_service, get_user_service
from app.services.room_type_service import RoomTypeService
from app.services.user_service import UserService


async def get_create_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
    user_service: UserService = Depends(get_user_service),
):
    return CreateRoomTypeUseCase(room_type_service, verify_csrf, current_user, user_service)


async def get_list_room_types_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
    user_service: UserService = Depends(get_user_service),
) -> ListRoomTypesUseCase:
    return ListRoomTypesUseCase(room_type_service, verify_csrf, current_user, user_service)


async def get_vendor_list_room_types_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorListRoomTypesUseCase:
    return VendorListRoomTypesUseCase(room_type_service, current_user)


async def get_vendor_create_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorCreateRoomTypeUseCase(room_type_service, verify_csrf, current_user)


async def get_vendor_update_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorUpdateRoomTypeUseCase(room_type_service, current_user)


async def get_vendor_delete_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorDeleteRoomTypeUseCase(room_type_service, current_user)


async def get_vendor_update_status_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_vendor),
):
    return VendorUpdateRoomTypeStatusUseCase(room_type_service, current_user)


async def get_update_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
    user_service: UserService = Depends(get_user_service),
):
    return UpdateRoomTypeUseCase(room_type_service, current_user, user_service)


async def get_update_status_room_type_use_case(
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
):
    return UpdateStatusRoomTypeUseCase(room_type_service, current_user)
