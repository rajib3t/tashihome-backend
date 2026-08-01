from fastapi import APIRouter, Depends, Form

from app.api.base_controller import BaseController
from app.application.dto.attributes.room_type import RoomTypeDTO, RoomTypeQueryDTO
from app.application.use_case.admin.attributes.attribute.create_room_type_use_case import CreateRoomTypeUseCase
from app.application.use_case.admin.attributes.attribute.get_room_type_use_case import ListRoomTypesUseCase
from app.application.use_case.admin.attributes.attribute.update_room_type_use_case import UpdateRoomTypeUseCase, UpdateStatusRoomTypeUseCase
from app.deps.room_type import get_create_room_type_use_case, get_list_room_types_use_case, get_update_room_type_use_case, get_update_status_room_type_use_case
from app.schemas.room_type_schema import RoomTypeListResponseSchema, RoomTypeResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class RoomTypeController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/room-types",
            tags=["Room Types"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_room_types, {"response_model": RoomTypeListResponseSchema}),
            ("post", "/", self._create_room_type, {"response_model": RoomTypeResponseSchema, "status_code": 201}),
            ("put", "/{room_type_id}", self._update_room_type, {"response_model": RoomTypeResponseSchema}),
            ("patch", "/{room_type_id}/{status}", self._update_room_type_status, {"response_model": RoomTypeResponseSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_room_types(
        self,
        params: RoomTypeQueryDTO = Depends(),
        use_case: ListRoomTypesUseCase = Depends(get_list_room_types_use_case),
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
        data: RoomTypeDTO ,
        use_case: CreateRoomTypeUseCase = Depends(get_create_room_type_use_case),
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
        data: RoomTypeDTO ,
        use_case: UpdateRoomTypeUseCase = Depends(get_update_room_type_use_case),
    ):
        room_type = await use_case.execute(room_type_id, data)
        return self.build_response(
            message="Room type updated successfully.",
            data=room_type,
        )

    @handle_api_exceptions
    async def _update_room_type_status(
        self,
        room_type_id: str,
        status: str,
        use_case: UpdateStatusRoomTypeUseCase = Depends(get_update_status_room_type_use_case),
    ):
        room_type = await use_case.execute(room_type_id, status)
        return self.build_response(
            message="Room type status updated successfully.",
            data=room_type,
        )


controller = RoomTypeController()
router = controller.router
