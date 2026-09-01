from fastapi import Depends

from app.application.use_case.admin.room_block.create_room_block_use_case import AdminCreateRoomBlockUseCase
from app.application.use_case.admin.room_block.delete_room_block_use_case import AdminDeleteRoomBlockUseCase
from app.application.use_case.admin.room_block.get_room_block_detail_use_case import AdminGetRoomBlockDetailUseCase
from app.application.use_case.admin.room_block.get_room_blocks_use_case import AdminGetRoomBlocksUseCase
from app.application.use_case.admin.room_block.update_room_block_use_case import AdminUpdateRoomBlockUseCase
from app.application.use_case.vendor.room_block.create_room_block_use_case import VendorCreateRoomBlockUseCase
from app.application.use_case.vendor.room_block.delete_room_block_use_case import VendorDeleteRoomBlockUseCase
from app.application.use_case.vendor.room_block.get_room_block_detail_use_case import VendorGetRoomBlockDetailUseCase
from app.application.use_case.vendor.room_block.get_room_blocks_use_case import VendorGetRoomBlocksUseCase
from app.application.use_case.vendor.room_block.update_room_block_use_case import VendorUpdateRoomBlockUseCase
from app.deps.auth import CurrentUser, require_admin_or_staff, require_vendor
from app.deps.service import (
    get_property_room_type_service,
    get_property_service,
    get_room_block_service,
    get_room_type_service,
)
from app.services.property_room_type_service import PropertyRoomTypeService
from app.services.property_service import PropertyService
from app.services.room_block_service import RoomBlockService
from app.services.room_type_service import RoomTypeService


# ─────────────────────────────────────────────
# Vendor Room Block Dependency Factories
# ─────────────────────────────────────────────

async def get_vendor_create_room_block_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    property_service: PropertyService = Depends(get_property_service),
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    property_room_type_service: PropertyRoomTypeService = Depends(get_property_room_type_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorCreateRoomBlockUseCase:
    return VendorCreateRoomBlockUseCase(
        room_block_service=room_block_service,
        property_service=property_service,
        room_type_service=room_type_service,
        property_room_type_service=property_room_type_service,
        current_user=current_user,
    )


async def get_vendor_room_blocks_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    property_service: PropertyService = Depends(get_property_service),
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorGetRoomBlocksUseCase:
    return VendorGetRoomBlocksUseCase(
        room_block_service=room_block_service,
        property_service=property_service,
        room_type_service=room_type_service,
        current_user=current_user,
    )


async def get_vendor_room_block_detail_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorGetRoomBlockDetailUseCase:
    return VendorGetRoomBlockDetailUseCase(
        room_block_service=room_block_service,
        current_user=current_user,
    )


async def get_vendor_update_room_block_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorUpdateRoomBlockUseCase:
    return VendorUpdateRoomBlockUseCase(
        room_block_service=room_block_service,
        current_user=current_user,
    )


async def get_vendor_delete_room_block_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorDeleteRoomBlockUseCase:
    return VendorDeleteRoomBlockUseCase(
        room_block_service=room_block_service,
        current_user=current_user,
    )


# ─────────────────────────────────────────────
# Admin Room Block Dependency Factories
# ─────────────────────────────────────────────

async def get_admin_create_room_block_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    property_service: PropertyService = Depends(get_property_service),
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    property_room_type_service: PropertyRoomTypeService = Depends(get_property_room_type_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> AdminCreateRoomBlockUseCase:
    return AdminCreateRoomBlockUseCase(
        room_block_service=room_block_service,
        property_service=property_service,
        room_type_service=room_type_service,
        property_room_type_service=property_room_type_service,
        current_user=current_user,
    )


async def get_admin_room_blocks_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    property_service: PropertyService = Depends(get_property_service),
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    _: CurrentUser = Depends(require_admin_or_staff),
) -> AdminGetRoomBlocksUseCase:
    return AdminGetRoomBlocksUseCase(
        room_block_service=room_block_service,
        property_service=property_service,
        room_type_service=room_type_service,
    )


async def get_admin_room_block_detail_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    _: CurrentUser = Depends(require_admin_or_staff),
) -> AdminGetRoomBlockDetailUseCase:
    return AdminGetRoomBlockDetailUseCase(
        room_block_service=room_block_service,
    )


async def get_admin_update_room_block_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    _: CurrentUser = Depends(require_admin_or_staff),
) -> AdminUpdateRoomBlockUseCase:
    return AdminUpdateRoomBlockUseCase(
        room_block_service=room_block_service,
    )


async def get_admin_delete_room_block_use_case(
    room_block_service: RoomBlockService = Depends(get_room_block_service),
    _: CurrentUser = Depends(require_admin_or_staff),
) -> AdminDeleteRoomBlockUseCase:
    return AdminDeleteRoomBlockUseCase(
        room_block_service=room_block_service,
    )

