from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.room_blocks.room_block import (
    RoomBlockCreateDTO,
    RoomBlockQueryDTO,
    RoomBlockUpdateDTO,
)
from app.application.use_case.admin.room_block.create_room_block_use_case import AdminCreateRoomBlockUseCase
from app.application.use_case.admin.room_block.delete_room_block_use_case import AdminDeleteRoomBlockUseCase
from app.application.use_case.admin.room_block.get_room_block_detail_use_case import AdminGetRoomBlockDetailUseCase
from app.application.use_case.admin.room_block.get_room_blocks_use_case import AdminGetRoomBlocksUseCase
from app.application.use_case.admin.room_block.update_room_block_use_case import AdminUpdateRoomBlockUseCase
from app.deps.room_block import (
    get_admin_create_room_block_use_case,
    get_admin_delete_room_block_use_case,
    get_admin_room_block_detail_use_case,
    get_admin_room_blocks_use_case,
    get_admin_update_room_block_use_case,
)
from app.schemas.room_block_schema import RoomBlockListResponseSchema, RoomBlockResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class AdminRoomBlockController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/room-blocks",
            tags=["Admin - Room Blocks"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_room_blocks, {"response_model": RoomBlockListResponseSchema}),
            ("post", "/", self._create_room_block, {"response_model": RoomBlockResponseSchema, "status_code": 201}),
            ("get", "/{room_block_id}", self._get_room_block, {"response_model": RoomBlockResponseSchema}),
            ("put", "/{room_block_id}", self._update_room_block, {"response_model": RoomBlockResponseSchema}),
            ("delete", "/{room_block_id}", self._delete_room_block, {"response_model": RoomBlockResponseSchema}),
        ]
        for method, path, handler, kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **kwargs)

    @handle_api_exceptions
    async def _get_room_blocks(
        self,
        params: RoomBlockQueryDTO = Depends(),
        use_case: AdminGetRoomBlocksUseCase = Depends(get_admin_room_blocks_use_case),
    ):
        page = await use_case.execute(params)
        return self.build_response(
            message="Room blocks retrieved successfully.",
            data=page.items,
            meta=self.pagination_meta(page),
        )

    @handle_api_exceptions
    async def _create_room_block(
        self,
        data: RoomBlockCreateDTO,
        use_case: AdminCreateRoomBlockUseCase = Depends(get_admin_create_room_block_use_case),
    ):
        room_block = await use_case.execute(data)
        return self.build_response(
            message="Room block created successfully.",
            data=room_block,
        )

    @handle_api_exceptions
    async def _get_room_block(
        self,
        room_block_id: str,
        use_case: AdminGetRoomBlockDetailUseCase = Depends(get_admin_room_block_detail_use_case),
    ):
        room_block = await use_case.execute(room_block_id)
        return self.build_response(
            message="Room block retrieved successfully.",
            data=room_block,
        )

    @handle_api_exceptions
    async def _update_room_block(
        self,
        room_block_id: str,
        data: RoomBlockUpdateDTO,
        use_case: AdminUpdateRoomBlockUseCase = Depends(get_admin_update_room_block_use_case),
    ):
        room_block = await use_case.execute(room_block_id, data)
        return self.build_response(
            message="Room block updated successfully.",
            data=room_block,
        )

    @handle_api_exceptions
    async def _delete_room_block(
        self,
        room_block_id: str,
        use_case: AdminDeleteRoomBlockUseCase = Depends(get_admin_delete_room_block_use_case),
    ):
        room_block = await use_case.execute(room_block_id)
        return self.build_response(
            message="Room block deleted successfully.",
            data=room_block,
        )


controller = AdminRoomBlockController()
router = controller.router

