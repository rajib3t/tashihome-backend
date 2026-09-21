from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.attributes.room_type import RoomTypeDTO, RoomTypeQueryDTO
from app.application.use_case.vendor.attributes.room_type.create_vendor_room_type_use_case import VendorCreateRoomTypeUseCase
from app.application.use_case.vendor.attributes.room_type.delete_vendor_room_type_use_case import VendorDeleteRoomTypeUseCase
from app.application.use_case.vendor.attributes.room_type.list_vendor_room_types_use_case import VendorListRoomTypesUseCase
from app.application.use_case.vendor.attributes.room_type.update_vendor_room_type_status_use_case import VendorUpdateRoomTypeStatusUseCase
from app.application.use_case.vendor.attributes.room_type.update_vendor_room_type_use_case import VendorUpdateRoomTypeUseCase
from app.deps.room_type import (
    get_vendor_create_room_type_use_case,
    get_vendor_delete_room_type_use_case,
    get_vendor_list_room_types_use_case,
    get_vendor_update_room_type_use_case,
    get_vendor_update_status_room_type_use_case,
)
from app.schemas.response import BaseResponse
from app.schemas.room_type_schema import RoomTypeListResponseSchema, RoomTypeResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class VendorRoomTypeController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/room-types",
            tags=["Vendor - Room Types"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_room_types, {"response_model": RoomTypeListResponseSchema}),
            ("post", "/", self._create_room_type, {"response_model": RoomTypeResponseSchema, "status_code": 201}),
            ("put", "/{room_type_id}", self._update_room_type, {"response_model": RoomTypeResponseSchema}),
            ("delete", "/{room_type_id}", self._delete_room_type, {"response_model": BaseResponse}),
            ("patch", "/{room_type_id}/{status}", self._update_room_type_status, {"response_model": RoomTypeResponseSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_room_types(
        self,
        params: RoomTypeQueryDTO = Depends(),
        use_case: VendorListRoomTypesUseCase = Depends(get_vendor_list_room_types_use_case),
    ):
        room_types = await use_case.execute(params)
        return self.build_response(
            message="Room types retrieved successfully.",
            data=room_types.items,
            meta=self.pagination_meta(room_types),
        )

    @handle_api_exceptions
    async def _create_room_type(
        self,
        data: RoomTypeDTO,
        use_case: VendorCreateRoomTypeUseCase = Depends(get_vendor_create_room_type_use_case),
    ):
        room_type = await use_case.execute(data)
        return self.build_response(
            message="Room type created successfully.",
            data=room_type,
        )

    @handle_api_exceptions
    async def _update_room_type(
        self,
        room_type_id: str,
        data: RoomTypeDTO,
        use_case: VendorUpdateRoomTypeUseCase = Depends(get_vendor_update_room_type_use_case),
    ):
        room_type = await use_case.execute(room_type_id, data)
        return self.build_response(
            message="Room type updated successfully.",
            data=room_type,
        )

    @handle_api_exceptions
    async def _delete_room_type(
        self,
        room_type_id: str,
        use_case: VendorDeleteRoomTypeUseCase = Depends(get_vendor_delete_room_type_use_case),
    ):
        await use_case.execute(room_type_id)
        return self.build_response(
            message="Room type deleted successfully.",
        )

    @handle_api_exceptions
    async def _update_room_type_status(
        self,
        room_type_id: str,
        status: str,
        use_case: VendorUpdateRoomTypeStatusUseCase = Depends(get_vendor_update_status_room_type_use_case),
    ):
        room_type = await use_case.execute(room_type_id, status)
        return self.build_response(
            message="Room type status updated successfully.",
            data=room_type,
        )


controller = VendorRoomTypeController()
router = controller.router