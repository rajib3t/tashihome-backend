from app.api.base_controller import BaseController

from app.application.dto.attributes.room_type import RoomTypeQueryDTO
from app.application.use_case.admin.attributes.attribute.get_room_type_use_case import ListRoomTypesUseCase
from app.deps.room_type import get_vendor_list_room_types_use_case
from app.schemas.room_type_schema import RoomTypeListResponseSchema
from app.utils.exception_decorate import handle_api_exceptions
from fastapi import APIRouter, Depends
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
            ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_room_types(
        self,
        params: RoomTypeQueryDTO = Depends(),
        use_case: ListRoomTypesUseCase = Depends(get_vendor_list_room_types_use_case),
    ):
        room_types = await use_case.execute(params)
        return self.build_response(
            message="Room types retrieved successfully.",
            data=room_types.items,
            meta=self.pagination_meta(room_types),
        )

controller = VendorRoomTypeController()
router = controller.router